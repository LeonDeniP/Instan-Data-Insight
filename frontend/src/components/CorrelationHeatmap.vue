<script setup>
import { computed } from 'vue'
const props = defineProps({ matrix: { type: Object, default: () => ({}) } })
const columnKeys = computed(() => Object.keys(props.matrix))

const getHeatmapBg = (val) => {
  if (val === 1) return 'bg-indigo-600 text-white'
  if (val >= 0.7) return 'bg-indigo-500/80 text-white'
  if (val >= 0.4) return 'bg-indigo-400/50 text-slate-800'
  if (val >= 0.1) return 'bg-indigo-200/30 text-slate-700'
  if (val <= -0.4) return 'bg-rose-400/50 text-slate-800'
  if (val <= -0.1) return 'bg-rose-200/30 text-slate-700'
  return 'bg-slate-50 text-slate-400'
}
</script>

<template>
  <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col overflow-hidden">
    <div class="mb-3">
      <h3 class="text-sm font-bold text-slate-800 tracking-tight">Pearson Correlation Matrix</h3>
      <p class="text-[11px] text-slate-400">Variansi linear antar variabel numerik (-1 hingga +1)</p>
    </div>
    <div v-if="columnKeys.length === 0" class="flex-1 flex items-center justify-center text-slate-400 text-xs italic py-12">
      Tidak ada fitur numerik terdeteksi.
    </div>
    <div v-else class="flex-1 overflow-auto">
      <div class="min-w-[400px]">
        <div class="flex">
          <div class="w-24 shrink-0"></div>
          <div v-for="col in columnKeys" :key="col" class="flex-1 p-1 text-[10px] font-black text-slate-500 text-center truncate uppercase font-mono">{{ col }}</div>
        </div>
        <div v-for="row in columnKeys" :key="row" class="flex items-center">
          <div class="w-24 shrink-0 text-[10px] font-black text-slate-500 truncate pr-2 text-right uppercase font-mono">{{ row }}</div>
          <div v-for="col in columnKeys" :key="col" :class="getHeatmapBg(matrix[row][col])" class="flex-1 p-2 text-center text-xs font-mono font-bold border border-white/40 transition-all rounded m-0.5 shadow-sm">
            {{ matrix[row][col] }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>