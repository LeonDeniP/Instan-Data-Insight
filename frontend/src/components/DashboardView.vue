<script setup>
defineProps({
  data: {
    type: Object,
    required: true
  }
})

// Helper untuk format angka desimal agar lebih rapi di UI
const formatNum = (val) => {
  if (val === null || val === undefined) return '-'
  return Number.isInteger(val) ? val : val.toFixed(2)
}
</script>

<template>
  <div class="space-y-8">
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-100 flex flex-col">
        <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Nama File</span>
        <span class="text-lg font-bold text-slate-800 mt-1 truncate">{{ data.filename }}</span>
      </div>
      <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-100 flex flex-col">
        <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Jumlah Baris</span>
        <span class="text-3xl font-extrabold text-indigo-600 mt-1">{{ data.summary.total_rows }}</span>
      </div>
      <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-100 flex flex-col">
        <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Jumlah Kolom</span>
        <span class="text-3xl font-extrabold text-emerald-600 mt-1">{{ data.summary.total_columns }}</span>
      </div>
    </div>

    <div v-if="data.statistics.length > 0" class="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
      <div class="px-6 py-4 border-b border-slate-100 bg-slate-50">
        <h3 class="text-base font-bold text-slate-800">Analisis Statistik (Kolom Numerik)</h3>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-slate-100 text-slate-600 uppercase text-xs font-bold">
              <th class="p-4">Nama Kolom</th>
              <th class="p-4 text-right">Rata-Rata (Mean)</th>
              <th class="p-4 text-right">Nilai Tengah (Median)</th>
              <th class="p-4 text-right">Min</th>
              <th class="p-4 text-right">Max</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 text-sm text-slate-700">
            <tr v-for="stat in data.statistics" :key="stat.column" class="hover:bg-slate-50 transition-colors">
              <td class="p-4 font-semibold text-slate-900">{{ stat.column }}</td>
              <td class="p-4 text-right">{{ formatNum(stat.mean) }}</td>
              <td class="p-4 text-right">{{ formatNum(stat.median) }}</td>
              <td class="p-4 text-right text-rose-600">{{ formatNum(stat.min) }}</td>
              <td class="p-4 text-right text-emerald-600">{{ formatNum(stat.max) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
      <div class="px-6 py-4 border-b border-slate-100 bg-slate-50">
        <h3 class="text-base font-bold text-slate-800">Struktur Data & Missing Values</h3>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-slate-100 text-slate-600 uppercase text-xs font-bold">
              <th class="p-4">Nama Kolom</th>
              <th class="p-4">Tipe Data</th>
              <th class="p-4 text-right">Missing Values (Kosong)</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 text-sm text-slate-700">
            <tr v-for="col in data.columns" :key="col.name" class="hover:bg-slate-50 transition-colors">
              <td class="p-4 font-medium text-slate-900">{{ col.name }}</td>
              <td class="p-4">
                <span class="px-2.5 py-1 text-xs font-semibold rounded-md bg-slate-100 text-slate-600">
                  {{ col.type }}
                </span>
              </td>
              <td class="p-4 text-right">
                <span :class="col.missing_values > 0 ? 'text-amber-600 font-bold' : 'text-slate-400'">
                  {{ col.missing_values }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>