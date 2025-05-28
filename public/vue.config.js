const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,
  publicPath: '/',
  
  // Fix CSS processing issues
  css: {
    extract: {
      // Ignore CSS order warnings
      ignoreOrder: true,
    },
    loaderOptions: {
      sass: {
        // Fix for older versions
        additionalData: `@import "~@/styles/variables.scss";`,
        sassOptions: {
          silenceDeprecations: ['legacy-js-api']
        }
      }
    }
  },

  // Webpack configuration to handle CSS issues
  configureWebpack: {
    optimization: {
      splitChunks: {
        chunks: 'all',
        cacheGroups: {
          vendor: {
            test: /[\\/]node_modules[\\/]/,
            name: 'vendors',
            priority: 10,
            chunks: 'all',
          },
          materialIcons: {
            test: /[\\/]node_modules[\\/]@mdi[\\/]/,
            name: 'material-icons',
            priority: 20,
            chunks: 'all',
          }
        }
      }
    },
    resolve: {
      fallback: {
        "path": false,
        "fs": false
      }
    }
  },

  // Chain webpack config for additional fixes
  chainWebpack: config => {
    // Handle CSS
    config.module
      .rule('css')
      .test(/\.css$/)
      .use('css-loader')
      .loader('css-loader')
      .options({
        importLoaders: 1,
        sourceMap: false
      })

    // Optimize chunks
    config.optimization.splitChunks({
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          priority: 10,
          chunks: 'all',
        }
      }
    })
  },

  // Production optimizations
  productionSourceMap: false,
  
  // Development server config
  devServer: {
    port: 8080,
    open: true
  }
})