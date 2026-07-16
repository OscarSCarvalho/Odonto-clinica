/* agenda.js — FullCalendar 6 integration */
(function () {
  'use strict';

  const CFG = window.AGENDA_CONFIG;

  // Cores de opacidade reduzida para eventos com status inativo
  const STATUS_OPACITY = { cancelado: 0.35, falta: 0.35 };

  // Cor de borda escurecida inline (sem server round-trip)
  function darken(hex, f) {
    const h = hex.replace('#', '');
    const r = Math.floor(parseInt(h.slice(0,2),16) * f);
    const g = Math.floor(parseInt(h.slice(2,4),16) * f);
    const b = Math.floor(parseInt(h.slice(4,6),16) * f);
    return `#${r.toString(16).padStart(2,'0')}${g.toString(16).padStart(2,'0')}${b.toString(16).padStart(2,'0')}`;
  }

  let expedientes = [];
  let profFiltroId = null;

  // Carrega expedientes uma vez para calcular businessHours
  async function carregarExpedientes() {
    const res = await fetch(CFG.expedientesUrl);
    expedientes = await res.json();
    return expedientes;
  }

  function businessHoursParaProfissional(profId) {
    if (!profId) {
      // Sem filtro: união de todos os expedientes
      return expedientes.map(e => ({
        daysOfWeek: e.daysOfWeek,
        startTime:  e.startTime,
        endTime:    e.endTime,
      }));
    }
    const exp = expedientes.find(e => e.profissional_id === parseInt(profId));
    if (!exp) return true;
    return [{ daysOfWeek: exp.daysOfWeek, startTime: exp.startTime, endTime: exp.endTime }];
  }

  function calcSlotMin(profId) {
    if (!profId) return '07:00:00';
    const exp = expedientes.find(e => e.profissional_id === parseInt(profId));
    return exp ? exp.startTime + ':00' : '07:00:00';
  }

  function calcSlotMax(profId) {
    if (!profId) return '20:00:00';
    const exp = expedientes.find(e => e.profissional_id === parseInt(profId));
    return exp ? exp.endTime + ':00' : '20:00:00';
  }

  function infoExpediente(profId) {
    const el = document.getElementById('expediente-info');
    if (!el) return;
    if (!profId) { el.textContent = ''; return; }
    const exp = expedientes.find(e => e.profissional_id === parseInt(profId));
    if (!exp) { el.textContent = ''; return; }
    const diasNome = ['Dom','Seg','Ter','Qua','Qui','Sex','Sáb'];
    const dias = exp.daysOfWeek.map(d => diasNome[d]).join(', ');
    el.textContent = `Expediente: ${exp.startTime}–${exp.endTime} | ${dias}`;
  }

  document.addEventListener('DOMContentLoaded', async function () {
    await carregarExpedientes();

    const calendarEl = document.getElementById('calendar');
    const filtro     = document.getElementById('filtro-profissional');

    const calendar = new FullCalendar.Calendar(calendarEl, {
      locale:       'pt-br',
      initialView:  'timeGridWeek',
      height:       'auto',
      nowIndicator: true,
      allDaySlot:   false,
      slotDuration: '00:15:00',
      slotMinTime:  calcSlotMin(null),
      slotMaxTime:  calcSlotMax(null),
      businessHours: businessHoursParaProfissional(null),
      headerToolbar: {
        left:   'prev,next today',
        center: 'title',
        right:  'dayGridMonth,timeGridWeek,timeGridDay',
      },
      buttonText: {
        today:  'Hoje',
        month:  'Mês',
        week:   'Semana',
        day:    'Dia',
        prev:   '‹',
        next:   '›',
      },

      // ── Eventos ──
      events: function (info, success, failure) {
        const start  = info.startStr.slice(0, 16).replace('T', ' ');
        const end    = info.endStr.slice(0, 16).replace('T', ' ');
        const profId = profFiltroId || '';
        const url    = `${CFG.eventosUrl}?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}` +
                       (profId ? `&profissional_id=${profId}` : '');
        fetch(url)
          .then(r => r.json())
          .then(success)
          .catch(failure);
      },

      // ── Visual pós-render do evento ──
      eventDidMount: function (info) {
        const status = info.event.extendedProps.status;
        const opacity = STATUS_OPACITY[status];
        if (opacity !== undefined) {
          info.el.style.opacity = opacity;
          info.el.style.textDecoration = 'line-through';
        }
        // Tooltip nativo
        info.el.title = [
          info.event.extendedProps.paciente,
          info.event.extendedProps.procedimento,
          info.event.extendedProps.profissional,
          `Status: ${status}`,
        ].join('\n');
      },

      // ── Clique num evento → editar ──
      eventClick: function (info) {
        window.location.href = `/agenda/editar/${info.event.id}`;
      },

      // ── Clique num slot livre → novo agendamento pré-preenchido ──
      dateClick: function (info) {
        if (calendar.view.type === 'dayGridMonth') return;
        const dt    = info.dateStr;           // "2026-07-21T09:00:00"
        const data  = dt.slice(0, 10);
        const hora  = dt.slice(11, 16);
        const profId = profFiltroId || '';
        let url = `${CFG.novUrl}?data=${data}&hora=${hora}`;
        if (profId) url += `&profissional_id=${profId}`;
        window.location.href = url;
      },
    });

    calendar.render();

    // ── Filtro de profissional ──
    filtro.addEventListener('change', function () {
      profFiltroId = this.value || null;
      infoExpediente(profFiltroId);

      // Atualiza businessHours e slot range dinamicamente
      calendar.setOption('businessHours', businessHoursParaProfissional(profFiltroId));
      calendar.setOption('slotMinTime',   calcSlotMin(profFiltroId));
      calendar.setOption('slotMaxTime',   calcSlotMax(profFiltroId));
      calendar.refetchEvents();
    });
  });
})();
