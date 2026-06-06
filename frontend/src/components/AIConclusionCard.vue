<script setup>
defineProps({ text: { type: String, default: '' } })
</script>

<template>
  <div class="bg-gradient-to-br from-indigo-900 to-slate-900 text-white p-6 rounded-2xl border border-indigo-700/50 shadow-xl relative overflow-hidden">
    <div class="flex items-center space-x-2 mb-3">
      <span class="flex h-2 w-2 relative">
        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
        <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
      </span>
      <h4 class="text-xs font-bold uppercase tracking-widest text-indigo-300">AI Executive Predictive Conclusion</h4>
    </div>
    <div class="prose prose-invert max-w-none text-sm leading-relaxed text-slate-200 whitespace-pre-line font-medium">
      {{ text }}
    </div>
  </div>
</template>