const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,
  
  publicPath: process.env.NODE_ENV === 'production' ? '/' : '/',
  outputDir: 'dist',

  devServer: {
    port: 8080,
    host: '0.0.0.0',
    allowedHosts: 'all'
  },

  css: {
    extract: process.env.NODE_ENV === 'production' ? {
      ignoreOrder: true,
    } : false,
    sourceMap: process.env.NODE_ENV !== 'production'
  },

  configureWebpack: {
    resolve: {
      alias: {
        '@': require('path').resolve(__dirname, 'src')
      }
    },
    performance: {
      hints: process.env.NODE_ENV === 'production' ? 'warning' : false,
      maxEntrypointSize: 512000,
      maxAssetSize: 512000
    }
  },

  chainWebpack: config => {
    config.plugins.delete('prefetch')
    
    if (process.platform === 'win32') {
      config.resolve.symlinks(false)
    }
  },

  productionSourceMap: false,
  lintOnSave: process.env.NODE_ENV !== 'production' ? 'warning' : false,
  parallel: require('os').cpus().length > 1
})
