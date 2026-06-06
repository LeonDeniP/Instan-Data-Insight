<script setup>
import { ref, onMounted, watch, nextTick, computed } from 'vue'
import { Chart, registerables } from 'chart.js'
import { marked } from 'marked'

// Mendaftarkan modul Chart.js
Chart.register(...registerables)

// ==========================================
// 1. GLOBAL STATE & NAVIGATION
// ==========================================
const currentView = ref('upload') // 'upload', 'dashboard', atau 'history'
const activeInsightData = ref(null)
const globalLoading = ref(false)
const historyList = ref([])

// State untuk Modal Pop-up Modern
const isModalOpen = ref(false)
const modalTitle = ref('')
const modalMessage = ref('')
const modalType = ref('info') // 'success' | 'error' | 'warning' | 'info'

// Fungsi untuk memicu Modal baru
const showAlertModal = (title, message, type = 'info') => {
  modalTitle.value = title
  modalMessage.value = message
  modalType.value = type
  isModalOpen.value = true
}

const closeModal = () => {
  isModalOpen.value = false
}

// ==========================================
// 2. CORE API LOGIC (App)
// ==========================================
const fetchHistory = async () => {
  try {
    const res = await fetch('http://127.0.0.1:8000/api/history')
    if (res.ok) historyList.value = await res.json()
  } catch (err) {
    console.error("Gagal memuat riwayat database MySQL:", err)
  }
}

const handleFileUpload = async (file) => {
  globalLoading.value = true
  const formData = new FormData()
  formData.append('file', file)

  try {
    const res = await fetch('http://127.0.0.1:8000/api/analyze', {
      method: 'POST',
      body: formData
    })
    if (res.ok) {
      activeInsightData.value = await res.json()
      currentView.value = 'dashboard'
      await fetchHistory()
      showAlertModal('Analisis Berhasil', 'Berkas Anda berhasil diproses dan dianalisis oleh AI Engine.', 'success')
    } else {
      const errData = await res.json()
      showAlertModal('Gagal Memproses', errData.detail || 'Terjadi gangguan internal pada server.', 'error')
    }
  } catch (err) {
    showAlertModal('Koneksi Gagal', 'Silakan periksa apakah server FastAPI Uvicorn port 8000 sudah berjalan.', 'error')
  } finally {
    globalLoading.value = false
  }
}

const loadHistoryDetail = async (id) => {
  globalLoading.value = true
  try {
    const res = await fetch(`http://127.0.0.1:8000/api/history/${id}`)
    if (res.ok) {
      activeInsightData.value = await res.json()
      currentView.value = 'dashboard'
    } else {
      showAlertModal('Unduh Gagal', 'Detail arsip insight gagal diunduh dari database.', 'error')
    }
  } catch (err) {
    showAlertModal('Gangguan Koneksi', 'Gagal menyambung ke API endpoint riwayat.', 'error')
  } finally {
    globalLoading.value = false
  }
}

const triggerCleanData = async (strategy) => {
  if (!activeInsightData.value?.id) return
  globalLoading.value = true
  try {
    const res = await fetch(`http://127.0.0.1:8000/api/clean/${activeInsightData.value.id}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ strategy })
    })
    if (res.ok) {
      activeInsightData.value = await res.json()
      showAlertModal('Restorasi Sukses', `Data berhasil disanitasi menggunakan metode Imputasi: ${strategy.toUpperCase()}`, 'success')
      await fetchHistory()
    }
  } catch (err) {
    showAlertModal('Operasi Gagal', 'Proses sanitasi atau pembersihan data mengalami kegagalan.', 'error')
  } finally {
    globalLoading.value = false
  }
}

const deleteRecord = async (id) => {
  if(!confirm("Apakah Anda yakin ingin menghapus insight ini secara permanen?")) return;
  
  try {
    const res = await fetch(`http://127.0.0.1:8000/api/history/${id}`, { method: 'DELETE' });
    if (res.ok) {
      showAlertModal('Dihapus', 'Data berhasil dihapus dari sistem repositori.', 'success');
      fetchHistory(); // Refresh daftar
    }
  } catch (err) {
    showAlertModal('Error', 'Gagal menghapus data dari sistem.', 'error');
  }
}

// ==========================================
// 3. UPLOAD COMPONENT LOGIC
// ==========================================
const isDragOver = ref(false)
const fileInput = ref(null)

const triggerSelectFile = () => fileInput.value.click()

const onFileChange = (e) => {
  if (e.target.files.length > 0) {
    validateAndProcess(e.target.files[0])
  }
}

const onDrop = (e) => {
  isDragOver.value = false
  if (e.dataTransfer.files.length > 0) {
    validateAndProcess(e.dataTransfer.files[0])
  }
}

const validateAndProcess = (file) => {
  if (!file.name.endsWith('.csv')) {
    showAlertModal('Format Ditolak', 'Sistem hanya menerima ekstensi dokumen berformat .csv', 'warning')
    return
  }
  handleFileUpload(file)
}

// ==========================================
// 4. DASHBOARD CHART & EXPORT LOGIC
// ==========================================
const chartCanvas = ref(null)
let chartInstance = null

const renderChart = () => {
  if (!activeInsightData.value?.statistics?.length || !chartCanvas.value) return
  if (chartInstance) chartInstance.destroy()

  const ctx = chartCanvas.value.getContext('2d')
  chartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: activeInsightData.value.statistics.map(s => s.column),
      datasets: [
        { 
          label: 'Rata-rata (Mean)', 
          data: activeInsightData.value.statistics.map(s => s.mean), 
          backgroundColor: 'rgba(79, 70, 229, 0.85)', 
          hoverBackgroundColor: 'rgba(79, 70, 229, 1)',
          borderRadius: 6,
          barPercentage: 0.6
        },
        { 
          label: 'Nilai Maks (Max)', 
          data: activeInsightData.value.statistics.map(s => s.max), 
          backgroundColor: 'rgba(16, 185, 129, 0.85)', 
          hoverBackgroundColor: 'rgba(16, 185, 129, 1)',
          borderRadius: 6,
          barPercentage: 0.6
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { 
        legend: { 
          position: 'top',
          labels: { font: { family: "'Inter', sans-serif", size: 12, weight: '600' }, usePointStyle: true, boxWidth: 8 } 
        },
        tooltip: {
          backgroundColor: 'rgba(15, 23, 42, 0.9)',
          titleFont: { size: 13, family: "'Inter', sans-serif" },
          bodyFont: { size: 12, family: "'Inter', sans-serif" },
          padding: 12,
          cornerRadius: 8
        }
      },
      scales: {
        y: { grid: { color: 'rgba(226, 232, 240, 0.6)', borderDash: [4, 4] }, ticks: { font: { family: "'Inter', sans-serif" } } },
        x: { grid: { display: false }, ticks: { font: { family: "'Inter', sans-serif" } } }
      }
    }
  })
}

const downloadPDF = () => {
  if (!activeInsightData.value?.id) return
  window.open(`http://127.0.0.1:8000/api/export-pdf/${activeInsightData.value.id}`, '_blank')
}

watch([activeInsightData, currentView], async ([newData, newView]) => {
  if (newData && newView === 'dashboard') { 
    await nextTick() 
    renderChart() 
  }
}, { deep: true, immediate: true })

// ==========================================
// 5. CORRELATION HEATMAP LOGIC
// ==========================================
const columnKeys = computed(() => Object.keys(activeInsightData.value?.correlation || {}))

const getHeatmapBg = (val) => {
  if (val === 1) return 'bg-indigo-600 text-white border-indigo-700'
  if (val >= 0.7) return 'bg-indigo-500 text-white border-indigo-600'
  if (val >= 0.4) return 'bg-indigo-300 text-indigo-900 border-indigo-400'
  if (val >= 0.1) return 'bg-indigo-100 text-indigo-800 border-indigo-200'
  if (val <= -0.4) return 'bg-rose-400 text-white border-rose-500'
  if (val <= -0.1) return 'bg-rose-200 text-rose-900 border-rose-300'
  return 'bg-slate-50 text-slate-400 border-slate-200'
}

const parsedAIConclusion = computed(() => {
  if (!activeInsightData.value?.ai_conclusion) return ''
  return marked.parse(activeInsightData.value.ai_conclusion)
})

onMounted(() => {
  fetchHistory()
})
</script>

<template>
  <div class="w-full min-h-screen bg-[#F8FAFC] text-slate-900 font-sans antialiased selection:bg-indigo-200 selection:text-indigo-900">
    <header class="bg-white/80 backdrop-blur-md border-b border-slate-200 sticky top-0 z-40 shadow-[0_1px_3px_0_rgba(0,0,0,0.02)] transition-all duration-300">
      <div class="mx-auto w-full mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        
        <div class="flex items-center space-x-3 cursor-pointer group" @click="currentView = 'upload'">
          <div class="bg-gradient-to-br from-indigo-600 to-violet-600 text-white p-2 rounded-xl font-black text-sm tracking-widest shadow-sm shadow-indigo-200 group-hover:scale-105 transition-transform duration-300 flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-5 h-5">
              <path fill-rule="evenodd" d="M2.25 13.5a8.25 8.25 0 0 1 8.25-8.25.75.75 0 0 1 .75.75v6.75H18a.75.75 0 0 1 .75.75 8.25 8.25 0 0 1-16.5 0Z" clip-rule="evenodd" />
              <path fill-rule="evenodd" d="M12.75 3a.75.75 0 0 1 .75-.75 8.25 8.25 0 0 1 8.25 8.25.75.75 0 0 1-.75.75h-7.5a.75.75 0 0 1-.75-.75V3Z" clip-rule="evenodd" />
            </svg>
          </div>
          <div class="flex flex-col">
            <span class="font-extrabold text-base text-slate-900 tracking-tight leading-none mb-0.5 group-hover:text-indigo-600 transition-colors">Instant Data Insight</span>
            <span class="text-[10px] text-slate-500 font-mono font-medium tracking-wide">Enterprise Analytics v3.0</span>
          </div>
        </div>

        <nav class="flex items-center space-x-1 sm:space-x-2 bg-slate-100/50 p-1 rounded-2xl border border-slate-200/60">
          <button @click="currentView = 'upload'" 
                  :class="currentView === 'upload' ? 'bg-white text-indigo-600 shadow-sm border-slate-200/50 font-bold' : 'text-slate-600 font-medium hover:text-slate-900 hover:bg-slate-200/50'" 
                  class="px-4 py-1.5 rounded-xl text-xs transition-all duration-200 border border-transparent flex items-center gap-1.5">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-4 h-4"><path stroke-linecap="round" stroke-linejoin="round" d="M12 16.5V9.75m0 0l3 3m-3-3l-3 3M6.75 19.5a4.5 4.5 0 01-1.41-8.775 5.25 5.25 0 0110.233-2.33 3 3 0 013.758 3.848A3.752 3.752 0 0118 19.5H6.75z" /></svg>
            Upload
          </button>
          
          <button v-if="activeInsightData" @click="currentView = 'dashboard'" 
                  :class="currentView === 'dashboard' ? 'bg-white text-indigo-600 shadow-sm border-slate-200/50 font-bold' : 'text-slate-600 font-medium hover:text-slate-900 hover:bg-slate-200/50'" 
                  class="px-4 py-1.5 rounded-xl text-xs transition-all duration-200 border border-transparent flex items-center gap-1.5">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-4 h-4"><path stroke-linecap="round" stroke-linejoin="round" d="M10.5 6a7.5 7.5 0 107.5 7.5h-7.5V6z" /><path stroke-linecap="round" stroke-linejoin="round" d="M13.5 10.5H21A7.5 7.5 0 0013.5 3v7.5z" /></svg>
            Dashboard
          </button>

          <button @click="currentView = 'history'" 
                  :class="currentView === 'history' ? 'bg-white text-indigo-600 shadow-sm border-slate-200/50 font-bold' : 'text-slate-600 font-medium hover:text-slate-900 hover:bg-slate-200/50'" 
                  class="px-4 py-1.5 rounded-xl text-xs transition-all duration-200 border border-transparent flex items-center gap-1.5">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-4 h-4"><path stroke-linecap="round" stroke-linejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75m-16.5-3.75v3.75m16.5 0v3.75C20.25 16.153 16.556 18 12 18s-8.25-1.847-8.25-4.125v-3.75m16.5 0c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125" /></svg>
            Repository
            <span :class="currentView === 'history' ? 'bg-indigo-100 text-indigo-700' : 'bg-slate-200 text-slate-600'" class="ml-1 font-mono text-[10px] px-1.5 py-0.5 rounded-md font-bold transition-colors">{{ historyList.length }}</span>
          </button>
        </nav>
      </div>
    </header>

    <main class="py-10 px-4 sm:px-6 w-full">
      
      <Transition enter-active-class="transition-opacity duration-300" enter-from-class="opacity-0" enter-to-class="opacity-100" leave-active-class="transition-opacity duration-300" leave-from-class="opacity-100" leave-to-class="opacity-0">
        <div v-if="globalLoading" class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center z-50">
          <div class="bg-white p-6 rounded-2xl shadow-2xl flex flex-col items-center space-y-4 border border-slate-100 min-w-[280px]">
            <div class="relative flex items-center justify-center h-12 w-12">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-30"></span>
              <svg class="animate-spin h-8 w-8 text-indigo-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </div>
            <div class="text-center">
              <span class="block text-sm font-bold text-slate-800">Memproses Data...</span>
              <span class="block text-[11px] text-slate-500 mt-1">Algoritma AI sedang bekerja</span>
            </div>
          </div>
        </div>
      </Transition>

      <div v-if="currentView === 'upload'" class="max-w-3xl mx-auto mt-8 sm:mt-16 animate-in fade-in slide-in-from-bottom-4 duration-500">
        <div class="mb-10 flex flex-col items-center"> 
          <div class="inline-flex items-center justify-center p-3 bg-indigo-50 rounded-2xl mb-4 shadow-sm border border-indigo-100">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-8 h-8 text-indigo-600">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
            </svg>
          </div>
          <h2 class="text-3xl font-black text-slate-900 tracking-tight text-center max-w-lg">Automated Data Science Engine</h2>
          <p class="text-sm text-center text-slate-500 mt-3 max-w-lg leading-relaxed">Unggah *dataset* CSV Anda untuk mendapatkan statistik deskriptif menyeluruh, pembersihan otomatis, dan laporan prediktif yang digerakkan oleh AI.</p>
        </div>

        <div 
          @click="triggerSelectFile" 
          @dragover.prevent="isDragOver = true" 
          @dragleave.prevent="isDragOver = false" 
          @drop.prevent="onDrop"
          :class="isDragOver ? 'border-indigo-500 bg-indigo-50/70 scale-[1.02] shadow-xl' : 'border-slate-300 bg-white hover:border-indigo-400 hover:bg-indigo-50/20 hover:shadow-md'"
          class="group border-2 border-dashed rounded-[2rem] p-16 text-center cursor-pointer transition-all duration-300 flex flex-col items-center justify-center relative overflow-hidden"
        >
          <div class="absolute -top-24 -right-24 w-48 h-48 bg-indigo-100/50 rounded-full blur-3xl group-hover:bg-indigo-200/50 transition-colors"></div>
          
          <input type="file" ref="fileInput" @change="onFileChange" accept=".csv" class="hidden" />
          
          <div :class="isDragOver ? 'bg-indigo-600 text-white scale-110' : 'bg-slate-100 text-slate-500 group-hover:bg-indigo-100 group-hover:text-indigo-600'" class="p-5 rounded-3xl mb-6 transition-all duration-300 shadow-sm relative z-10">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 16.5V9.75m0 0l3 3m-3-3l-3 3M6.75 19.5a4.5 4.5 0 01-1.41-8.775 5.25 5.25 0 0110.233-2.33 3 3 0 013.758 3.848A3.752 3.752 0 0118 19.5H6.75z" />
            </svg>
          </div>
          <p class="text-base font-bold text-slate-800 relative z-10">
            <span class="text-indigo-600 group-hover:underline underline-offset-4 decoration-2">Klik untuk mencari file</span> atau seret dokumen ke area ini
          </p>
          <p class="text-xs text-slate-500 mt-2 font-medium relative z-10">File CSV standar didukung hingga 50MB</p>
          
          <div class="flex items-center gap-2 mt-6 relative z-10">
            <span class="px-2.5 py-1 bg-slate-100 text-slate-500 font-mono text-[10px] font-bold rounded-md border border-slate-200">.CSV</span>
            <span class="px-2.5 py-1 bg-slate-100 text-slate-500 font-mono text-[10px] font-bold rounded-md border border-slate-200">UTF-8</span>
          </div>
        </div>
      </div>

      <div v-if="currentView === 'dashboard' && activeInsightData" class="space-y-6 max-w-[90rem] mx-auto animate-in fade-in duration-500">
        
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-4 sm:px-6 sm:py-5 rounded-2xl border border-slate-200 shadow-sm">
          <div class="flex items-center gap-4">
            <div class="hidden sm:flex p-3 bg-indigo-50 text-indigo-600 rounded-xl border border-indigo-100">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" /></svg>
            </div>
            <div>
              <h2 class="text-xl font-black text-slate-900 tracking-tight">Workspace Analitik</h2>
              <div class="flex items-center gap-2 mt-1">
                <span class="inline-flex w-2 h-2 rounded-full bg-emerald-500"></span>
                <p class="text-xs text-slate-500 font-medium font-mono truncate max-w-xs sm:max-w-md">{{ activeInsightData.filename }}</p>
              </div>
            </div>
          </div>
          
          <div class="flex flex-wrap items-center gap-2 sm:gap-3">
            <div class="flex bg-slate-100 p-1 rounded-xl border border-slate-200">
              <button @click="triggerCleanData('mean')" class="px-3 py-1.5 hover:bg-white text-slate-700 text-xs font-semibold rounded-lg transition-all focus:ring-2 focus:ring-indigo-500/50">Imputasi Mean</button>
              <button @click="triggerCleanData('median')" class="px-3 py-1.5 hover:bg-white text-slate-700 text-xs font-semibold rounded-lg transition-all focus:ring-2 focus:ring-indigo-500/50">Imputasi Median</button>
            </div>
            
            <button @click="triggerCleanData('drop_outliers')" class="px-3 py-1.5 bg-amber-50 hover:bg-amber-100 text-amber-700 border border-amber-200/60 text-xs font-bold rounded-xl transition-all flex items-center gap-1.5 shadow-sm">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-3.5 h-3.5"><path stroke-linecap="round" stroke-linejoin="round" d="M14.25 6.087c0-.355.186-.676.401-.959.221-.29.349-.634.349-1.003 0-1.036-1.007-1.875-2.25-1.875s-2.25.84-2.25 1.875c0 .369.128.713.349 1.003.215.283.401.604.401.959v0a1.5 1.5 0 01-1.5 1.5H8.25m6 0h.01M10.5 18.375h.008v.008h-.008v-.008zm3 0h.008v.008h-.008v-.008zm3 0h.008v.008h-.008v-.008z" /></svg>
              Pangkas Outliers
            </button>
            
            <button @click="downloadPDF" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-xl transition-all shadow-md shadow-indigo-200 flex items-center gap-2 focus:ring-2 focus:ring-offset-2 focus:ring-indigo-600">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-4 h-4"><path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" /></svg>
              Unduh Report
            </button>
          </div>
        </div>

        <div v-if="activeInsightData.ai_conclusion" class="bg-slate-900 rounded-2xl shadow-xl relative overflow-hidden border border-slate-800">
          <div class="absolute inset-0 bg-gradient-to-br from-indigo-500/10 via-transparent to-purple-500/10 pointer-events-none"></div>
          <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-emerald-400"></div>
          
          <div class="p-6 sm:p-8 relative z-10">
            <div class="flex items-center gap-3 mb-4">
              <div class="p-2 bg-indigo-500/20 rounded-lg border border-indigo-500/30">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5 text-indigo-300"><path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.428-1.428L13.5 18.75l1.183-.394a2.25 2.25 0 001.428-1.428l.394-1.183.394 1.183a2.25 2.25 0 001.428 1.428l1.183.394-1.183.394a2.25 2.25 0 00-1.428 1.428z" /></svg>
              </div>
              <h4 class="text-[13px] font-bold uppercase tracking-widest text-slate-300">Executive AI Insight</h4>
              <span class="flex h-2 w-2 relative ml-auto sm:ml-0">
                <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
            </div>
            <div 
              class="prose prose-invert max-w-none text-sm leading-relaxed text-slate-300 font-medium border-l-2 border-indigo-500/30 pl-4"
              v-html="parsedAIConclusion"
            ></div>
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-6">
          <div class="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between group hover:-translate-y-1 transition-transform duration-300 cursor-default">
            <div>
              <span class="text-[11px] font-bold text-slate-400 uppercase tracking-widest block mb-1">Total Baris Data</span>
              <p class="text-3xl font-black text-indigo-600 tracking-tight">{{ activeInsightData.summary?.total_rows?.toLocaleString() }} <span class="text-sm text-slate-400 font-semibold tracking-normal">Record</span></p>
            </div>
            <div class="p-4 bg-indigo-50 rounded-xl text-indigo-300 group-hover:bg-indigo-100 group-hover:text-indigo-500 transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-8 h-8"><path stroke-linecap="round" stroke-linejoin="round" d="M8.25 6.75h12M8.25 12h12m-12 5.25h12M3.75 6.75h.007v.008H3.75V6.75zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zM3.75 12h.007v.008H3.75V12zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm-.375 5.25h.007v.008H3.75v-.008zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z" /></svg>
            </div>
          </div>
          
          <div class="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between group hover:-translate-y-1 transition-transform duration-300 cursor-default">
            <div>
              <span class="text-[11px] font-bold text-slate-400 uppercase tracking-widest block mb-1">Lebar Matriks Fitur</span>
              <p class="text-3xl font-black text-emerald-600 tracking-tight">{{ activeInsightData.summary?.total_columns }} <span class="text-sm text-slate-400 font-semibold tracking-normal">Kolom</span></p>
            </div>
            <div class="p-4 bg-emerald-50 rounded-xl text-emerald-300 group-hover:bg-emerald-100 group-hover:text-emerald-500 transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-8 h-8"><path stroke-linecap="round" stroke-linejoin="round" d="M9 4.5v15m6-15v15m-10.875 0h15.75c.621 0 1.125-.504 1.125-1.125V5.625c0-.621-.504-1.125-1.125-1.125H4.125C3.504 4.5 3 5.004 3 5.625v12.75c0 .621.504 1.125 1.125 1.125z" /></svg>
            </div>
          </div>
          
          <div class="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between group hover:-translate-y-1 transition-transform duration-300 cursor-default overflow-hidden">
            <div class="min-w-0 pr-4">
              <span class="text-[11px] font-bold text-slate-400 uppercase tracking-widest block mb-1">Identitas Log Dokumen</span>
              <p class="text-base font-bold text-slate-800 mt-3 truncate bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200 font-mono shadow-inner inline-block">ID_X{{ activeInsightData.id }}</p>
            </div>
            <div class="p-4 bg-slate-50 rounded-xl text-slate-300 group-hover:bg-slate-100 group-hover:text-slate-500 transition-colors shrink-0">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-8 h-8"><path stroke-linecap="round" stroke-linejoin="round" d="M7.5 14.25v2.25m3-4.5v4.5m3-6.75v6.75m3-9v9M6 20.25h12A2.25 2.25 0 0020.25 18V6A2.25 2.25 0 0018 3.75H6A2.25 2.25 0 003.75 6v12A2.25 2.25 0 006 20.25z" /></svg>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div class="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col">
            <div class="mb-6 flex items-center justify-between">
              <div>
                <h3 class="text-base font-black text-slate-900">Distribusi Nilai Numerik</h3>
                <p class="text-xs text-slate-500 mt-0.5">Perbandingan Mean & Max tiap variabel.</p>
              </div>
              <div class="p-2 bg-slate-50 rounded-lg text-slate-400">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-5 h-5"><path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" /></svg>
              </div>
            </div>
            <div class="relative h-72 w-full flex-1">
              <canvas ref="chartCanvas"></canvas>
            </div>
          </div>

          <div class="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col overflow-hidden">
            <div class="mb-6 flex items-center justify-between">
              <div>
                <h3 class="text-base font-black text-slate-900 tracking-tight">Pearson Correlation Matrix</h3>
                <p class="text-xs text-slate-500 mt-0.5">Korelasi linear antar fitur numerik (-1 hingga +1)</p>
              </div>
              <div class="p-2 bg-slate-50 rounded-lg text-slate-400">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-5 h-5"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" /></svg>
              </div>
            </div>
            
            <div v-if="columnKeys.length === 0" class="flex-1 flex flex-col items-center justify-center text-slate-400 text-xs italic py-12 bg-slate-50/50 rounded-xl border border-dashed border-slate-200">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-8 h-8 mb-2 text-slate-300"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
              Tidak ada fitur numerik terdeteksi.
            </div>
            <div v-else class="flex-1 overflow-auto rounded-xl border border-slate-200 bg-slate-50/30 p-2">
              <div class="min-w-max">
                <div class="flex">
                  <div class="w-24 shrink-0"></div>
                  <div v-for="col in columnKeys" :key="col" class="w-14 p-1 text-[9px] font-black text-slate-500 text-center truncate uppercase font-mono pb-2">{{ col }}</div>
                </div>
                <div v-for="row in columnKeys" :key="row" class="flex items-center mb-0.5">
                  <div class="w-24 shrink-0 text-[10px] font-bold text-slate-600 truncate pr-3 text-right uppercase font-mono bg-transparent" :title="row">{{ row }}</div>
                  <div class="flex gap-0.5">
                    <div v-for="col in columnKeys" :key="col" 
                         :class="getHeatmapBg(activeInsightData.correlation[row][col])" 
                         class="w-14 h-8 flex items-center justify-center text-[10px] font-mono font-bold transition-all rounded-[4px] hover:scale-110 hover:shadow-md cursor-crosshair z-10 hover:z-20 border">
                      {{ activeInsightData.correlation[row][col] }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
          <div class="px-6 py-5 border-b border-slate-200 bg-slate-50/50 flex justify-between items-center">
            <div class="flex items-center gap-3">
              <div class="p-2 bg-indigo-100 text-indigo-600 rounded-lg">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-5 h-5"><path stroke-linecap="round" stroke-linejoin="round" d="M10.125 2.25h-4.5c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125v-9M10.125 2.25h.375a9 9 0 019 9v.375M10.125 2.25A3.375 3.375 0 0113.5 5.625v1.5c0 .621.504 1.125 1.125 1.125h1.5a3.375 3.375 0 013.375 3.375M9 15l2.25 2.25L15 12" /></svg>
              </div>
              <div>
                <h3 class="text-base font-black text-slate-900">Data Quality Auditor</h3>
                <p class="text-xs text-slate-500 mt-0.5">Pemindaian kebersihan dataset otomatis pada setiap fitur.</p>
              </div>
            </div>
            <span class="text-[10px] bg-emerald-100 text-emerald-700 px-3 py-1.5 rounded-full font-bold uppercase tracking-wider flex items-center gap-1 border border-emerald-200">
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> Validated
            </span>
          </div>
          
          <div class="overflow-x-auto">
            <table class="w-full text-left border-collapse min-w-[600px]">
              <thead>
                <tr class="bg-slate-50 text-slate-500 text-[11px] font-bold uppercase tracking-wider border-b border-slate-200">
                  <th class="px-6 py-4 w-1/3">Feature Name</th>
                  <th class="px-6 py-4 w-1/4">Schema Type</th>
                  <th class="px-6 py-4 text-center w-1/6">Missing Value</th>
                  <th class="px-6 py-4 text-right">Anomalies Detected</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100 text-sm bg-white">
                <tr v-for="col in activeInsightData.columns" :key="col.name" class="hover:bg-slate-50/80 transition-colors group">
                  <td class="px-6 py-4 font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">{{ col.name }}</td>
                  <td class="px-6 py-4">
                    <span class="px-2.5 py-1 bg-slate-100 text-slate-600 text-[11px] rounded-md font-mono font-semibold border border-slate-200/60 inline-block">{{ col.type }}</span>
                  </td>
                  <td class="px-6 py-4 text-center">
                    <span v-if="col.missing_values > 0" class="inline-flex items-center justify-center px-2.5 py-1 bg-amber-100 text-amber-700 text-xs font-bold rounded-full border border-amber-200 min-w-[40px]">
                      {{ col.missing_values }}
                    </span>
                    <span v-else class="text-slate-400 font-medium">-</span>
                  </td>
                  <td class="px-6 py-4 text-right">
                    <span v-if="col.anomaly_count > 0" class="inline-flex items-center gap-1.5 px-3 py-1 bg-rose-50 text-rose-700 text-xs font-bold rounded-full border border-rose-200">
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-3.5 h-3.5"><path fill-rule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd" /></svg>
                      {{ col.anomaly_count }} outliers
                    </span>
                    <span v-else class="inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-50 text-emerald-700 text-xs font-bold rounded-full border border-emerald-200">
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-3.5 h-3.5"><path fill-rule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clip-rule="evenodd" /></svg>
                      Clean
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div v-if="currentView === 'history'" class="max-w-4xl mx-auto space-y-6 animate-in fade-in duration-500">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <div>
            <h2 class="text-2xl font-black text-slate-900 tracking-tight">Repository Analytics</h2>
            <p class="text-sm text-slate-500 mt-1">Arsip riwayat *dataset* yang telah sukses dieksekusi oleh mesin AI.</p>
          </div>
          <div class="p-3 bg-indigo-50 rounded-xl text-indigo-500 border border-indigo-100 hidden sm:block">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6"><path stroke-linecap="round" stroke-linejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75m-16.5-3.75v3.75m16.5 0v3.75C20.25 16.153 16.556 18 12 18s-8.25-1.847-8.25-4.125v-3.75m16.5 0c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125" /></svg>
          </div>
        </div>

        <div v-if="historyList.length === 0" class="bg-white rounded-2xl border border-dashed border-slate-300 p-16 text-center shadow-sm">
          <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-slate-50 mb-4 text-slate-300">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-8 h-8"><path stroke-linecap="round" stroke-linejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75m-16.5-3.75v3.75m16.5 0v3.75C20.25 16.153 16.556 18 12 18s-8.25-1.847-8.25-4.125v-3.75m16.5 0c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125" /></svg>
          </div>
          <h3 class="text-base font-bold text-slate-900 mb-1">Belum Ada Riwayat</h3>
          <p class="text-sm text-slate-500">Lakukan proses unggah data setidaknya satu kali untuk melihat arsip di sini.</p>
        </div>

        <div v-else class="space-y-3">
          <div v-for="item in historyList" :key="item.id" class="bg-white p-4 sm:p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between group hover:border-indigo-300 hover:shadow-md transition-all duration-300 gap-4">
            
            <div class="flex items-start sm:items-center gap-4 min-w-0">
              <div class="p-3 bg-slate-50 text-slate-400 rounded-xl border border-slate-100 group-hover:bg-indigo-50 group-hover:text-indigo-600 group-hover:border-indigo-100 transition-colors shrink-0">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" /></svg>
              </div>
              <div class="min-w-0">
                <p class="text-base font-bold text-slate-900 truncate group-hover:text-indigo-600 transition-colors">{{ item.filename }}</p>
                <div class="flex flex-wrap items-center gap-2 sm:gap-3 mt-1.5">
                  <span class="font-mono text-[10px] font-bold text-slate-600 bg-slate-100 px-2 py-0.5 rounded-md border border-slate-200 flex items-center gap-1">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-3 h-3 text-slate-400"><path fill-rule="evenodd" d="M10 2.5c-1.31 0-2.526.386-3.546 1.051a.75.75 0 01-.82-1.256A8 8 0 0118 9a22.47 22.47 0 01-1.228 7.351.75.75 0 11-1.417-.49A20.97 20.97 0 0016.5 9 6.5 6.5 0 0110 2.5zM4.333 4.802a.75.75 0 01.981-.331A7.085 7.085 0 0110 5.5a7.085 7.085 0 014.686-1.029.75.75 0 11-.331 1.463A5.584 5.584 0 0010 7a5.584 5.584 0 00-3.686-.103.75.75 0 01-.981-.331zM6 11a4 4 0 118 0 15.353 15.353 0 01-.883 5.093.75.75 0 11-1.405-.52A13.856 13.856 0 0012.5 11a2.5 2.5 0 10-5 0c0 1.623.275 3.19.782 4.654a.75.75 0 01-1.413.513A15.353 15.353 0 016 11z" clip-rule="evenodd" /></svg>
                    ID_X{{ item.id }}
                  </span>
                  <span class="text-[11px] text-slate-500 font-medium flex items-center gap-1">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-3 h-3 text-slate-400"><path fill-rule="evenodd" d="M1 5.25A2.25 2.25 0 013.25 3h13.5A2.25 2.25 0 0119 5.25v9.5A2.25 2.25 0 0116.75 17H3.25A2.25 2.25 0 011 14.75v-9.5zm1.5 5.81v3.69c0 .414.336.75.75.75h13.5a.75.75 0 00.75-.75v-2.69l-2.22-2.219a2.25 2.25 0 00-3.182 0l-1.44 1.439a2.25 2.25 0 01-3.182 0X8.06 9.06a2.25 2.25 0 00-3.182 0l-2.379 2.378zM17.5 9.44l-2.28-2.28a.75.75 0 00-1.06 0l-1.44 1.44a.75.75 0 01-1.06 0L8.06 5.06a.75.75 0 00-1.06 0l-4.5 4.5v-4.31a.75.75 0 01.75-.75h13.5c.414 0 .75.336.75.75v4.19z" clip-rule="evenodd" /></svg>
                    {{ item.total_rows }} x {{ item.total_columns }}
                  </span>
                  <span class="text-[11px] text-slate-400 hidden md:inline">&bull;</span>
                  <span class="text-[11px] text-slate-500 font-medium flex items-center gap-1">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-3 h-3 text-slate-400"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm.75-13a.75.75 0 00-1.5 0v5c0 .414.336.75.75.75h4a.75.75 0 000-1.5h-3.25V5z" clip-rule="evenodd" /></svg>
                    {{ item.uploaded_at }}
                  </span>
                </div>
              </div>
            </div>

            <div class="flex items-center gap-2 shrink-0 ml-12 sm:ml-0 border-t border-slate-100 sm:border-0 pt-3 sm:pt-0">
              <button @click="loadHistoryDetail(item.id)" class="px-4 py-2 bg-indigo-50 hover:bg-indigo-600 text-indigo-700 hover:text-white text-xs font-bold rounded-xl transition-colors focus:ring-2 focus:ring-offset-1 focus:ring-indigo-500">
                Buka Insight
              </button>
              <button @click="deleteRecord(item.id)" class="p-2 text-slate-400 hover:text-white hover:bg-rose-500 rounded-xl transition-colors focus:ring-2 focus:ring-offset-1 focus:ring-rose-500" title="Hapus Permanen">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-5 h-5"><path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" /></svg>
              </button>
            </div>
            
          </div>
        </div>
      </div>

    </main>

    <Transition enter-active-class="transition-opacity duration-300" enter-from-class="opacity-0" enter-to-class="opacity-100" leave-active-class="transition-opacity duration-200" leave-from-class="opacity-100" leave-to-class="opacity-0">
      <div v-if="isModalOpen" class="fixed inset-0 z-[60] flex items-center justify-center p-4">
        <div class="fixed inset-0 bg-slate-900/50 backdrop-blur-sm" @click="closeModal"></div>
        
        <Transition enter-active-class="transition-all duration-300" enter-from-class="opacity-0 scale-95 translate-y-4" enter-to-class="opacity-100 scale-100 translate-y-0" leave-active-class="transition-all duration-200" leave-from-class="opacity-100 scale-100 translate-y-0" leave-to-class="opacity-0 scale-95 translate-y-4" appear>
          <div class="bg-white rounded-[1.5rem] shadow-2xl border border-slate-100 max-w-md w-full p-6 sm:p-8 relative z-10 overflow-hidden">
            
            <div class="absolute top-0 left-0 w-full h-1.5" :class="{
              'bg-emerald-500': modalType === 'success',
              'bg-rose-500': modalType === 'error',
              'bg-amber-400': modalType === 'warning',
              'bg-indigo-500': modalType === 'info'
            }"></div>

            <div class="flex items-start space-x-4">
              <div class="p-3.5 rounded-2xl shrink-0 border" :class="{
                'bg-emerald-50 text-emerald-600 border-emerald-100': modalType === 'success',
                'bg-rose-50 text-rose-600 border-rose-100': modalType === 'error',
                'bg-amber-50 text-amber-500 border-amber-100': modalType === 'warning',
                'bg-indigo-50 text-indigo-600 border-indigo-100': modalType === 'info'
              }">
                <svg v-if="modalType === 'success'" xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                <svg v-else-if="modalType === 'error'" xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                <svg v-else-if="modalType === 'warning'" xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
              </div>
              
              <div class="flex-1 min-w-0 pt-1">
                <h3 class="text-lg font-black text-slate-900 leading-tight tracking-tight">{{ modalTitle }}</h3>
                <p class="text-sm text-slate-500 mt-2 leading-relaxed">{{ modalMessage }}</p>
              </div>
            </div>
            
            <div class="mt-8 flex justify-end">
              <button @click="closeModal" class="px-5 py-2.5 text-sm font-bold bg-slate-900 text-white rounded-xl hover:bg-slate-800 transition-all shadow-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-900 w-full sm:w-auto text-center">
                Mengerti, Lanjutkan
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </div>
</template>

<style>
/* Font Inter import standar untuk modern feel */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

body {
  font-family: 'Inter', sans-serif;
}

/* Custom Scrollbar for Heatmap & Table */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}
::-webkit-scrollbar-track {
  background: #f1f5f9; 
  border-radius: 4px;
}
::-webkit-scrollbar-thumb {
  background: #cbd5e1; 
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
  background: #94a3b8; 
}
</style>