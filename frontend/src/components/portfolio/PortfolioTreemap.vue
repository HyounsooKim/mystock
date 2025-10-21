<template>
  <div ref="chartRef" class="portfolio-treemap" :style="{ height: chartHeight }"></div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  holdings: {
    type: Array,
    required: true,
    default: () => []
  },
  chartHeight: {
    type: String,
    default: '400px'
  },
  title: {
    type: String,
    default: ''
  }
})

const chartRef = ref(null)
let chartInstance = null

const initChart = () => {
  if (!chartRef.value) {
    console.log('Chart ref not available')
    return
  }
  
  if (!props.holdings || props.holdings.length === 0) {
    console.log('No holdings data:', props.holdings)
    return
  }
  
  console.log('Holdings data:', props.holdings)
  
  // Dispose existing chart
  if (chartInstance) {
    chartInstance.dispose()
  }
  
  chartInstance = echarts.init(chartRef.value)
  
  // Prepare data for treemap
  const data = props.holdings
    .filter(h => {
      const hasValue = h.current_value && h.current_value > 0
      console.log(`Filtering ${h.symbol}: current_value=${h.current_value}, hasValue=${hasValue}`)
      return hasValue
    })
    .map(holding => {
      const returnRate = Number(holding.return_rate) || 0
      const profitLoss = Number(holding.profit_loss) || 0
      const quantity = Number(holding.quantity) || 0
      const avgPrice = Number(holding.avg_price) || 0
      const currentPrice = Number(holding.current_price) || 0
      const currentValue = Number(holding.current_value) || 0
      
      console.log(`Mapping ${holding.symbol}:`, {
        returnRate,
        profitLoss,
        quantity,
        avgPrice,
        currentPrice,
        currentValue
      })
      
      return {
        name: holding.symbol,
        value: currentValue,
        returnRate: returnRate,
        profitLoss: profitLoss,
        quantity: quantity,
        avgPrice: avgPrice,
        currentPrice: currentPrice,
        companyName: holding.company_name || holding.symbol
      }
    })
  
  console.log('Treemap data after filtering and mapping:', data)
  
  if (data.length === 0) {
    chartInstance.dispose()
    chartInstance = null
    return
  }
  
  const option = {
    tooltip: {
      formatter: (params) => {
        const data = params.data
        if (!data) return ''
        
        const isProfit = (data.profitLoss || 0) >= 0
        const color = isProfit ? '#2fb344' : '#d63939'
        
        return `
          <div style="padding: 8px;">
            <div style="font-weight: bold; margin-bottom: 8px; font-size: 14px;">
              ${data.name || ''}
            </div>
            <div style="font-size: 12px; color: #666; margin-bottom: 4px;">
              ${data.companyName || ''}
            </div>
            <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #eee;">
              <div>수량: ${(data.quantity || 0).toLocaleString()}</div>
              <div>평균단가: ${formatCurrency(data.avgPrice || 0)}</div>
              <div>현재가: ${formatCurrency(data.currentPrice || 0)}</div>
              <div style="margin-top: 4px; padding-top: 4px; border-top: 1px solid #eee;">
                <div style="color: ${color}; font-weight: bold;">
                  수익률: ${(data.returnRate || 0) >= 0 ? '+' : ''}${(data.returnRate || 0).toFixed(2)}%
                </div>
                <div style="color: ${color};">
                  손익: ${(data.profitLoss || 0) >= 0 ? '+' : ''}${formatCurrency(data.profitLoss || 0)}
                </div>
              </div>
            </div>
          </div>
        `
      }
    },
    series: [
      {
        type: 'treemap',
        width: '100%',
        height: '100%',
        roam: false,
        nodeClick: false,
        breadcrumb: {
          show: false
        },
        label: {
          show: true,
          fontSize: 14,
          fontWeight: 'bold',
          color: '#fff',
          formatter: (params) => {
            if (!params.data) return ''
            const returnRate = params.data.returnRate || 0
            const sign = returnRate >= 0 ? '+' : ''
            return `{name|${params.name}}\n{rate|${sign}${Number(returnRate).toFixed(2)}%}`
          },
          rich: {
            name: {
              fontSize: 14,
              fontWeight: 'bold',
              lineHeight: 20
            },
            rate: {
              fontSize: 12,
              lineHeight: 18
            }
          }
        },
        upperLabel: {
          show: false
        },
        itemStyle: {
          borderColor: '#fff',
          borderWidth: 2,
          gapWidth: 2
        },
        levels: [
          {
            itemStyle: {
              borderWidth: 0,
              gapWidth: 2
            }
          },
          {
            itemStyle: {
              borderWidth: 2,
              gapWidth: 2,
              borderColorSaturation: 0.6
            }
          }
        ],
        data: data.map(item => ({
          ...item,
          itemStyle: {
            color: getColorByReturnRate(item.returnRate)
          }
        })),
        visualMin: -10,
        visualMax: 10,
        visualDimension: 'returnRate'
      }
    ]
  }
  
  console.log('Chart option:', option)
  chartInstance.setOption(option)
}

// Get color based on return rate
const getColorByReturnRate = (rate) => {
  if (rate >= 10) return '#1a8a1a'      // Deep green
  if (rate >= 5) return '#267326'       // Dark green
  if (rate >= 2) return '#336633'       // Medium dark green
  if (rate >= 1) return '#3d5c3d'       // Dark greenish
  if (rate >= 0.5) return '#4d4d4d'     // Dark gray
  if (rate >= -0.5) return '#1a1a1a'    // Almost black (near 0%)
  if (rate >= -1) return '#4d3d3d'      // Dark grayish red
  if (rate >= -2) return '#663333'      // Medium dark red
  if (rate >= -5) return '#732626'      // Dark red
  if (rate >= -10) return '#8a1a1a'     // Deep red
  return '#8a1a1a'                       // Deep red
}

const formatCurrency = (value) => {
  if (value === null || value === undefined) return '-'
  
  // Check if it's a US stock (assume if value is less than 1000, it's USD)
  if (value < 1000) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(value)
  }
  
  return new Intl.NumberFormat('ko-KR', {
    style: 'currency',
    currency: 'KRW'
  }).format(value)
}

const handleResize = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (chartInstance) {
    chartInstance.dispose()
  }
})

watch(() => props.holdings, () => {
  initChart()
}, { deep: true })
</script>

<style scoped>
.portfolio-treemap {
  width: 100%;
}
</style>
