<script setup>
import { ref, nextTick, watch } from 'vue'
import { Chart, registerables } from 'chart.js'
import AIConclusionCard from './AIConclusionCard.vue'
import DataQualityTable from './DataQualityTable.vue'
import CorrelationHeatmap from './CorrelationHeatmap.vue'

Chart.register(...registerables)

const props = defineProps({ dataInsight: { type: Object, default: null } })
const emit = defineEmits(['trigger-clean'])

const chartCanvas = ref(null)
let chartInstance = null

const renderChart = () => {
  if (!props.dataInsight?.statistics?.length || !chartCanvas.value) return
  if (chartInstance) chartInstance.destroy()

  const ctx = chartCanvas.value.getContext('2d')
  chartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: props.dataInsight.statistics.map(s => s.column),
      datasets: [
        { label: 'Rata-rata (Mean)', data: props.dataInsight.statistics.map(s => s.mean), backgroundColor: 'rgba(79, 70, 229, 0.85)', borderRadius: 6 },
        { label: 'Nilai Maks (Max)', data: props.dataInsight.statistics.map(s => s.max), backgroundColor: 'rgba(16, 185, 129, 0.85)', borderRadius: 6 }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { labels: { font: { size: 11, weight: '600' } } } }
    }
  })
}

const downloadPDF = () => {
  if (!props.dataInsight?.id) return
  window.open(`http://127.0.0.1:8000/api/export-pdf/${props.dataInsight.id}`, '_blank')
}

watch(() => props.dataInsight, async (newData) => {
  if (newData) { await nextTick(); renderChart() }
}, { deep: true, immediate: true })
</script>

<template>
  <div class="space-y-6 max-w-7xl mx-auto">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
      <div>
        <h2 class="text-lg font-black text-slate-800">Workspace Analisis Aktif</h2>
        <p class="text-xs text-slate-500 font-medium">Berkas: {{ dataInsight?.filename }}</p>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <button @click="emit('trigger-clean', 'mean')" class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-xl transition-all">Imputasi Mean</button>
        <button @click="emit('trigger-clean', 'median')" class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-xl transition-all">Imputasi Median</button>
        <button @click="emit('trigger-clean', 'drop_outliers')" class="px-3 py-1.5 bg-amber-50 hover:bg-amber-100 text-amber-700 text-xs font-bold rounded-xl transition-all">Pangkas Outliers (IQR)</button>
        <button @click="downloadPDF" class="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-xl transition-all shadow-md flex items-center space-x-1">
          <span>Unduh PDF Report</span>
        </button>
      </div>
    </div>

    <AIConclusionCard v-if="dataInsight?.ai_conclusion" :text="dataInsight.ai_conclusion" />

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
      <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
        <span class="text-[10px] font-bold text-slate-400 uppercase tracking-widest block">Ukuran Baris Data</span>
        <p class="text-2xl font-black text-indigo-600 mt-0.5">{{ dataInsight?.summary?.total_rows?.toLocaleString() }} <span class="text-xs text-slate-400 font-medium">Record</span></p>
      </div>
      <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
        <span class="text-[10px] font-bold text-slate-400 uppercase tracking-widest block">Lebar Matriks Fitur</span>
        <p class="text-2xl font-black text-emerald-600 mt-0.5">{{ dataInsight?.summary?.total_columns }} <span class="text-xs text-slate-400 font-medium">Kolom</span></p>
      </div>
      <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
        <span class="text-[10px] font-bold text-slate-400 uppercase tracking-widest block">Identitas Log Dokumen</span>
        <p class="text-sm font-bold text-slate-700 mt-2 truncate bg-slate-50 px-2.5 py-1 rounded-lg border border-slate-100 font-mono">ID_REF_X{{ dataInsight?.id }}</p>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col">
        <h3 class="text-sm font-bold text-slate-800 mb-4">Kalkulasi Variansi Nilai Deskriptif</h3>
        <div class="relative h-64 w-full flex-1">
          <canvas ref="chartCanvas"></canvas>
        </div>
      </div>
      <CorrelationHeatmap :matrix="dataInsight?.correlation" />
    </div>

    <DataQualityTable :columnsData="dataInsight?.columns" />
  </div>
</template>