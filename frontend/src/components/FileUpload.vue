<script setup>
import { ref } from 'vue'

const emit = defineEmits(['file-selected'])
const isDragOver = ref(false)
const fileInput = ref(null)

const triggerSelectFile = () => {
  fileInput.value.click()
}

const onFileChange = (e) => {
  if (e.target.files.length > 0) {
    validateAndEmit(e.target.files[0])
  }
}

const onDrop = (e) => {
  isDragOver.value = false
  if (e.dataTransfer.files.length > 0) {
    validateAndEmit(e.dataTransfer.files[0])
  }
}

const validateAndEmit = (file) => {
  // REVISI: Menggunakan .endsWith() dengan 'S' besar
  if (!file.name.endsWith('.csv')) {
    alert('Format file ditolak! Sistem hanya menerima ekstensi .csv')
    return
  }
  emit('file-selected', file)
}
</script>

<template>
  <div class="max-w-2xl mx-auto mt-10">
    <div class="text-center mb-8">
      <h2 class="text-2xl font-black text-slate-800">Automated Data Science Engine</h2>
      <p class="text-xs text-slate-500 mt-1">Unggah file CSV Anda untuk dihitung secara statistik deskriptif dan didiagnosis oleh AI.</p>
    </div>

    <div 
      @click="triggerSelectFile" 
      @dragover.prevent="isDragOver = true" 
      @dragleave.prevent="isDragOver = false" 
      @drop.prevent="onDrop"
      :class="isDragOver ? 'border-indigo-500 bg-indigo-50/50 scale-[1.01]' : 'border-slate-300 bg-white hover:border-indigo-400'"
      class="border-2 border-dashed rounded-3xl p-12 text-center cursor-pointer transition-all duration-200 flex flex-col items-center justify-center shadow-sm"
    >
      <input type="file" ref="fileInput" @change="onFileChange" accept=".csv" class="hidden" />
      <div :class="isDragOver ? 'bg-indigo-600 text-white' : 'bg-slate-50 text-slate-400'" class="p-4 rounded-2xl mb-4">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
      </div>
      <p class="text-sm font-bold text-slate-700">
        <span class="text-indigo-600">Klik untuk memilih berkas</span> atau seret file ke sini
      </p>
      <p class="text-[11px] text-slate-400 mt-1 font-mono">Mendukung dokumen .CSV hingga 50MB</p>
    </div>
  </div>
</template>