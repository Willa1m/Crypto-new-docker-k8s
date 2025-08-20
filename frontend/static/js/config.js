// API配置文件
const API_CONFIG = {
    // API基础URL - 生产环境使用相对路径，开发环境可指定完整URL
    BASE_URL: '', // 使用相对路径，通过Nginx代理
    
    // API端点配置
    ENDPOINTS: {
        // 健康检查
        HEALTH: '/api/health',
        
        // 价格相关
        LATEST_PRICES: '/api/latest_prices',
        PRICE_HISTORY: '/api/chart_data',
        
        // 图表数据
        CHART_DATA_BTC: '/api/btc_data',
        CHART_DATA_ETH: '/api/eth_data',
        CHART_DATA_KLINE: '/api/kline_data',
        
        // 分析报告
        ANALYSIS_REPORT: '/api/analysis_report',
        
        // 系统状态
        SYSTEM_STATUS: '/api/system/status',
        CACHE_STATUS: '/api/cache/status',
        CACHE_CLEAR: '/api/cache/clear'
    },
    
    // 请求配置
    REQUEST_CONFIG: {
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        timeout: 30000 // 30秒超时
    }
};

// 导出配置（如果使用模块系统）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = API_CONFIG;
}