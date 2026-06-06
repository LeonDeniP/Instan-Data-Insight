<script setup>
defineProps({ historyItems: { type: Array, default: () => [] } })
const emit = defineEmits(['select-history'])
</script>

<template>
  <div class="max-w-4xl mx-auto space-y-4">
    <div>
      <h2 class="text-xl font-black text-slate-800">Historical Data Analytics Repository</h2>
      <p class="text-xs text-slate-500">Daftar rekaman metadata berkas yang sukses masuk audit di database MySQL.</p>
    </div>
    <div v-if="historyItems.length === 0" class="bg-white rounded-2xl border border-slate-200 p-12 text-center text-slate-400 text-xs italic">
      Belum ada riwayat aktivitas unggahan di workspace ini.
    </div>
    <div v-else class="grid grid-cols-1 gap-3">
      <div v-for="item in historyItems" :key="item.id" class="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between group hover:border-indigo-300 transition-all">
        <div class="flex items-center space-x-4 min-w-0">
          <div class="p-3 bg-indigo-50 text-indigo-600 rounded-xl group-hover:bg-indigo-600 group-hover:text-white transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
          </div>
          <div class="min-w-0">
            <p class="text-sm font-bold text-slate-800 truncate">{{ item.filename }}</p>
            <div class="flex items-center space-x-3 text-[11px] text-slate-400 mt-0.5">
              <span class="font-mono font-bold text-indigo-600 bg-slate-50 px-1.5 py-0.5 rounded border border-slate-100">ID ##{{ item.id }}</span>
              <span>Dimensi: {{ item.total_rows }} x {{ item.total_columns }}</span>
              <span>Waktu: {{ item.uploaded_at }}</span>
            </div>
          </div>
        </div>
        <button @click="emit('select-history', item.id)" class="px-4 py-1.5 border border-slate-200 hover:border-indigo-600 text-slate-600 hover:text-indigo-600 text-xs font-bold rounded-xl bg-slate-50 hover:bg-white transition-all shrink-0">
          Buka Insight
        </button>
      </div>
    </div>
  </div>
</template>