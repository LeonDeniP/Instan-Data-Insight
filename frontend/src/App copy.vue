<script setup>
import { ref, onMounted, watch, nextTick, computed } from 'vue'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

const currentView = ref('upload')
const activeInsightData = ref(null)
const globalLoading = ref(false)
const historyList = ref([])

const isModalOpen = ref(false)
const modalTitle = ref('')
const modalMessage = ref('')
const modalType = ref('info')

const isDeleteModalOpen = ref(false)
const deleteTargetId = ref(null)

const showAlertModal = (title, message, type = 'info') => {
  modalTitle.value = title
  modalMessage.value = message
  modalType.value = type
  isModalOpen.value = true
}

const closeModal = () => {
  isModalOpen.value = false
}

const openDeleteModal = (id) => {
  deleteTargetId.value = id
  isDeleteModalOpen.value = true
}

const closeDeleteModal = () => {
  deleteTargetId.value = null
  isDeleteModalOpen.value = false
}

const fetchHistory = async () => {
  try {
    const res = await fetch('http://127.0.0.1:8000/api/history')

    if (res.ok) {
      historyList.value = await res.json()
    }
  } catch (err) {
    console.error('Gagal memuat riwayat database MySQL:', err)
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

      showAlertModal(
        'Analisis Berhasil',
        'Berkas berhasil diproses dan dianalisis oleh AI Engine.',
        'success'
      )
    } else {
      const errData = await res.json()

      showAlertModal(
        'Gagal Memproses',
        errData.detail || 'Terjadi gangguan internal pada server.',
        'error'
      )
    }
  } catch (err) {
    showAlertModal(
      'Koneksi Gagal',
      'Pastikan server FastAPI pada port 8000 sedang berjalan.',
      'error'
    )
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
      showAlertModal(
        'Gagal Memuat',
        'Detail insight gagal dimuat dari database.',
        'error'
      )
    }
  } catch (err) {
    showAlertModal(
      'Gangguan Koneksi',
      'Gagal terhubung ke endpoint riwayat.',
      'error'
    )
  } finally {
    globalLoading.value = false
  }
}

const triggerCleanData = async (strategy) => {
  if (!activeInsightData.value?.id) return

  globalLoading.value = true

  try {
    const res = await fetch(
      `http://127.0.0.1:8000/api/clean/${activeInsightData.value.id}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ strategy })
      }
    )

    if (res.ok) {
      activeInsightData.value = await res.json()

      showAlertModal(
        'Restorasi Berhasil',
        `Data berhasil dibersihkan menggunakan metode ${strategy.toUpperCase()}.`,
        'success'
      )

      await fetchHistory()
    }
  } catch (err) {
    showAlertModal(
      'Operasi Gagal',
      'Proses pembersihan data mengalami kegagalan.',
      'error'
    )
  } finally {
    globalLoading.value = false
  }
}

const confirmDelete = async () => {
  if (!deleteTargetId.value) return

  try {
    const res = await fetch(
      `http://127.0.0.1:8000/api/history/${deleteTargetId.value}`,
      {
        method: 'DELETE'
      }
    )

    if (res.ok) {
      showAlertModal(
        'Data Dihapus',
        'Insight berhasil dihapus dari repository.',
        'success'
      )

      await fetchHistory()

      if (activeInsightData.value?.id === deleteTargetId.value) {
        activeInsightData.value = null
        currentView.value = 'history'
      }
    } else {
      showAlertModal(
        'Gagal Menghapus',
        'Data tidak dapat dihapus.',
        'error'
      )
    }
  } catch (err) {
    showAlertModal(
      'Gagal Menghapus',
      'Terjadi kesalahan saat menghapus data.',
      'error'
    )
  } finally {
    closeDeleteModal()
  }
}

const isDragOver = ref(false)
const fileInput = ref(null)

const triggerSelectFile = () => {
  fileInput.value?.click()
}

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
  if (!file.name.toLowerCase().endsWith('.csv')) {
    showAlertModal(
      'Format Ditolak',
      'Sistem hanya menerima file dengan ekstensi .csv',
      'warning'
    )
    return
  }

  handleFileUpload(file)
}

const chartCanvas = ref(null)
let chartInstance = null

const renderChart = () => {
  if (!activeInsightData.value?.statistics?.length) return
  if (!chartCanvas.value) return

  if (chartInstance) {
    chartInstance.destroy()
  }

  const ctx = chartCanvas.value.getContext('2d')

  chartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: activeInsightData.value.statistics.map(
        stat => stat.column
      ),
      datasets: [
        {
          label: 'Mean',
          data: activeInsightData.value.statistics.map(
            stat => stat.mean
          ),
          backgroundColor: 'rgba(79,70,229,0.85)',
          borderRadius: 8
        },
        {
          label: 'Maximum',
          data: activeInsightData.value.statistics.map(
            stat => stat.max
          ),
          backgroundColor: 'rgba(16,185,129,0.85)',
          borderRadius: 8
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: {
            font: {
              size: 12,
              weight: '600'
            }
          }
        }
      }
    }
  })
}

const downloadPDF = () => {
  if (!activeInsightData.value?.id) return

  window.open(
    `http://127.0.0.1:8000/api/export-pdf/${activeInsightData.value.id}`,
    '_blank'
  )
}

watch(
  [activeInsightData, currentView],
  async ([newData, newView]) => {
    if (newData && newView === 'dashboard') {
      await nextTick()
      renderChart()
    }
  },
  {
    deep: true,
    immediate: true
  }
)

const columnKeys = computed(() =>
  Object.keys(activeInsightData.value?.correlation || {})
)

const getHeatmapBg = (val) => {
  if (val === 1) return 'bg-indigo-600 text-white'
  if (val >= 0.7) return 'bg-indigo-500/80 text-white'
  if (val >= 0.4) return 'bg-indigo-400/50 text-slate-800'
  if (val >= 0.1) return 'bg-indigo-200/30 text-slate-700'
  if (val <= -0.4) return 'bg-rose-400/50 text-slate-800'
  if (val <= -0.1) return 'bg-rose-200/30 text-slate-700'

  return 'bg-slate-50 text-slate-400'
}

onMounted(() => {
  fetchHistory()
})
</script>

<template>
  <div class="min-h-screen bg-slate-50 text-slate-900 font-sans antialiased">
    <header class="bg-white border-b border-slate-200 sticky top-0 z-40 shadow-sm">
      <div class="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <div class="flex items-center space-x-3 cursor-pointer" @click="currentView = 'upload'">
          <div class="bg-indigo-600 text-white p-2 rounded-xl font-black text-sm tracking-wider shadow-md">IDI</div>
          <span class="font-extrabold text-base text-slate-800 tracking-tight">Instant Data Insight <span class="text-xs text-indigo-600 font-mono">v3.0 Modular</span></span>
        </div>
        <nav class="flex items-center space-x-2">
          <button @click="currentView = 'upload'" :class="currentView === 'upload' ? 'bg-indigo-50 text-indigo-600 font-bold' : 'text-slate-600 font-medium hover:bg-slate-50'" class="px-4 py-2 rounded-xl text-xs transition-all">Upload</button>
          <button v-if="activeInsightData" @click="currentView = 'dashboard'" :class="currentView === 'dashboard' ? 'bg-indigo-50 text-indigo-600 font-bold' : 'text-slate-600 font-medium hover:bg-slate-50'" class="px-4 py-2 rounded-xl text-xs transition-all">Dashboard</button>
          <button @click="currentView = 'history'" :class="currentView === 'history' ? 'bg-indigo-50 text-indigo-600 font-bold' : 'text-slate-600 font-medium hover:bg-slate-50'" class="px-4 py-2 rounded-xl text-xs transition-all flex items-center space-x-2">
            <span>Repository</span>
            <span class="bg-slate-200 text-slate-700 font-mono text-[10px] px-1.5 py-0.5 rounded-full font-bold">{{ historyList.length }}</span>
          </button>
        </nav>
      </div>
    </header>

    <main class="py-8 px-6">
      <div v-if="globalLoading" class="fixed inset-0 bg-slate-900/20 backdrop-blur-sm flex items-center justify-center z-50">
        <div class="bg-white p-6 rounded-2xl shadow-xl flex items-center space-x-4 border border-slate-100">
          <div class="animate-spin h-5 w-5 border-2 border-indigo-600 border-t-transparent rounded-full"></div>
          <span class="text-xs font-bold text-slate-700">Sedang Menganalisis Algoritma AI & Statistik Big Data...</span>
        </div>
      </div>

      <div v-if="currentView === 'upload'" class="max-w-2xl mx-auto mt-10">
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

      <div v-if="currentView === 'dashboard' && activeInsightData" class="space-y-6 max-w-7xl mx-auto">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
          <div>
            <h2 class="text-lg font-black text-slate-800">Workspace Analisis Aktif</h2>
            <p class="text-xs text-slate-500 font-medium">Berkas: {{ activeInsightData.filename }}</p>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <button @click="triggerCleanData('mean')" class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-xl transition-all">Imputasi Mean</button>
            <button @click="triggerCleanData('median')" class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-xl transition-all">Imputasi Median</button>
            <button @click="triggerCleanData('drop_outliers')" class="px-3 py-1.5 bg-amber-50 hover:bg-amber-100 text-amber-700 text-xs font-bold rounded-xl transition-all">Pangkas Outliers (IQR)</button>
            <button @click="downloadPDF" class="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-xl transition-all shadow-md flex items-center space-x-1">
              <span>Unduh PDF Report</span>
            </button>
          </div>
        </div>

        <div v-if="activeInsightData.ai_conclusion" class="bg-gradient-to-br from-indigo-900 to-slate-900 text-white p-6 rounded-2xl border border-indigo-700/50 shadow-xl relative overflow-hidden">
          <div class="flex items-center space-x-2 mb-3">
            <span class="flex h-2 w-2 relative">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <h4 class="text-xs font-bold uppercase tracking-widest text-indigo-300">AI Executive Predictive Conclusion</h4>
          </div>
          <div class="prose prose-invert max-w-none text-sm leading-relaxed text-slate-200 whitespace-pre-line font-medium">
            {{ activeInsightData.ai_conclusion }}
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
            <span class="text-[10px] font-bold text-slate-400 uppercase tracking-widest block">Ukuran Baris Data</span>
            <p class="text-2xl font-black text-indigo-600 mt-0.5">{{ activeInsightData.summary?.total_rows?.toLocaleString() }} <span class="text-xs text-slate-400 font-medium">Record</span></p>
          </div>
          <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
            <span class="text-[10px] font-bold text-slate-400 uppercase tracking-widest block">Lebar Matriks Fitur</span>
            <p class="text-2xl font-black text-emerald-600 mt-0.5">{{ activeInsightData.summary?.total_columns }} <span class="text-xs text-slate-400 font-medium">Kolom</span></p>
          </div>
          <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
            <span class="text-[10px] font-bold text-slate-400 uppercase tracking-widest block">Identitas Log Dokumen</span>
            <p class="text-sm font-bold text-slate-700 mt-2 truncate bg-slate-50 px-2.5 py-1 rounded-lg border border-slate-100 font-mono">ID_REF_X{{ activeInsightData.id }}</p>
          </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col">
            <h3 class="text-sm font-bold text-slate-800 mb-4">Kalkulasi Variansi Nilai Deskriptif</h3>
            <div class="relative h-64 w-full flex-1">
              <canvas ref="chartCanvas"></canvas>
            </div>
          </div>

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
                  <div v-for="col in columnKeys" :key="col" :class="getHeatmapBg(activeInsightData.correlation[row][col])" class="flex-1 p-2 text-center text-xs font-mono font-bold border border-white/40 transition-all rounded m-0.5 shadow-sm">
                    {{ activeInsightData.correlation[row][col] }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

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
                <tr v-for="col in activeInsightData.columns" :key="col.name" class="hover:bg-slate-50/80 transition-colors">
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
      </div>

      <div v-if="currentView === 'history'" class="max-w-4xl mx-auto space-y-4">
        <div>
          <h2 class="text-xl font-black text-slate-800">Historical Data Analytics Repository</h2>
          <p class="text-xs text-slate-500">Daftar rekaman metadata berkas yang sukses masuk audit di database MySQL.</p>
        </div>
        <div v-if="historyList.length === 0" class="bg-white rounded-2xl border border-slate-200 p-12 text-center text-slate-400 text-xs italic">
          Belum ada riwayat aktivitas unggahan di workspace ini.
        </div>
        <div v-else class="grid grid-cols-1 gap-3">
          <div v-for="item in historyList" :key="item.id" class="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between group hover:border-indigo-300 transition-all">
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
            <button @click="loadHistoryDetail(item.id)" class="px-4 py-1.5 border border-slate-200 hover:border-indigo-600 text-slate-600 hover:text-indigo-600 text-xs font-bold rounded-xl bg-slate-50 hover:bg-white transition-all shrink-0">
              Buka Insight
            </button>
            <button @click="deleteRecord(item.id)" class="text-rose-500 text-xs font-bold">Hapus</button>
          </div>
        </div>
      </div>
    </main>

    <div v-if="isModalOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm transition-opacity" @click="closeModal"></div>
      
      <div class="bg-white rounded-2xl shadow-2xl border border-slate-100 max-w-md w-full p-6 relative z-10 transform scale-100 transition-all animate-in fade-in zoom-in-95 duration-150">
        <div class="flex items-start space-x-4">
          <div class="p-3 rounded-xl shrink-0" :class="{
            'bg-emerald-50 text-emerald-600': modalType === 'success',
            'bg-rose-50 text-rose-600': modalType === 'error',
            'bg-amber-50 text-amber-500': modalType === 'warning',
            'bg-indigo-50 text-indigo-600': modalType === 'info'
          }">
            <svg v-if="modalType === 'success'" xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            <svg v-else-if="modalType === 'error'" xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            <svg v-else-if="modalType === 'warning'" xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          </div>
          
          <div class="flex-1 min-w-0">
            <h3 class="text-base font-black text-slate-900 leading-6">{{ modalTitle }}</h3>
            <p class="text-xs text-slate-500 mt-2 leading-relaxed">{{ modalMessage }}</p>
          </div>
        </div>
        
        <div class="mt-6 flex justify-end">
          <button @click="closeModal" class="px-4 py-2 text-xs font-bold bg-slate-900 text-white rounded-xl hover:bg-slate-800 transition-all shadow-md focus:outline-none focus:ring-2 focus:ring-slate-400">
            Mengerti
          </button>
        </div>
      </div>
    </div>
  </div>
</template>