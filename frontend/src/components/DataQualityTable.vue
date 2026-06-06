<script setup>
defineProps({ columnsData: { type: Array, default: () => [] } })
</script>

<template>
  <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
    <div class="px-6 py-4 border-b border-slate-100 bg-slate-50 flex justify-between items-center">
      <h3 class="text-sm font-bold text-slate-800">Data Quality Auditor</h3>
      <span class="text-xs bg-indigo-50 text-indigo-600 px-2.5 py-1 rounded-full font-semibold">Automated Audit</span>
    </div>
    <div class="overflow-x-auto">
      <table class="w-full text-left border-collapse">
        <thead>
          <tr class="bg-slate-50/50 text-slate-400 text-xs font-bold uppercase border-b border-slate-200">
            <th class="px-6 py-3.5">Feature Name</th>
            <th class="px-6 py-3.5">Schema Type</th>
            <th class="px-6 py-3.5 text-center">Missing Row</th>
            <th class="px-6 py-3.5 text-right">Anomalies Detected</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100 text-sm">
          <tr v-for="col in columnsData" :key="col.name" class="hover:bg-slate-50/80 transition-colors">
            <td class="px-6 py-3.5 font-bold text-slate-900">{{ col.name }}</td>
            <td class="px-6 py-3.5"><span class="px-2 py-0.5 bg-slate-100 text-slate-600 text-xs rounded font-mono border border-slate-200">{{ col.type }}</span></td>
            <td class="px-6 py-3.5 text-center font-medium" :class="col.missing_values > 0 ? 'text-amber-600' : 'text-slate-500'">{{ col.missing_values }}</td>
            <td class="px-6 py-3.5 text-right font-bold" :class="col.anomaly_count > 0 ? 'text-rose-600' : 'text-emerald-600'">
              {{ col.anomaly_count > 0 ? `${col.anomaly_count} outliers` : 'Clean' }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>