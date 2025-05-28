const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,
  
  // Public path for deployment
  publicPath: process.env.NODE_ENV === 'production' 
    ? '/' 
    : '/',

  // Output directory for Firebase Hosting
  outputDir: 'dist',

  // Development server configuration
  devServer: {
    port: 8080,
    host: '0.0.0.0',
    allowedHosts: 'all',
    proxy: {
      // Proxy API calls to Firebase Functions during development
      '/api': {
        target: process.env.VUE_APP_API_BASE_URL || 'http://localhost:5001/your-project-id/us-central1',
        changeOrigin: true,
        secure: false,
        logLevel: 'debug'
      }
    }
  },

  // PWA Configuration
  pwa: {
    name: 'Afya Medical EHR',
    themeColor: '#2E8B57',
    msTileColor: '#2E8B57',
    appleMobileWebAppCapable: 'yes',
    appleMobileWebAppStatusBarStyle: 'default',
    
    workboxPluginMode: 'InjectManifest',
    workboxOptions: {
      swSrc: 'src/sw.js',
    },

    manifestOptions: {
      name: 'Afya Medical EHR',
      short_name: 'Afya EHR',
      description: 'Ghana Healthcare Electronic Records System',
      display: 'standalone',
      orientation: 'portrait',
      theme_color: '#2E8B57',
      background_color: '#ffffff',
      start_url: '/',
      icons: [
        {
          src: './img/icons/android-chrome-192x192.png',
          sizes: '192x192',
          type: 'image/png'
        },
        {
          src: './img/icons/android-chrome-512x512.png',
          sizes: '512x512',
          type: 'image/png'
        }
      ]
    }
  },

  // Webpack configuration
  configureWebpack: {
    optimization: {
      splitChunks: {
        chunks: 'all',
        cacheGroups: {
          vendor: {
            test: /[\\/]node_modules[\\/]/,
            name: 'vendors',
            chunks: 'all',
            priority: 10
          },
          vuetify: {
            test: /[\\/]node_modules[\\/]vuetify[\\/]/,
            name: 'vuetify',
            chunks: 'all',
            priority: 20
          }
        }
      }
    },
    
    // Performance hints
    performance: {
      hints: process.env.NODE_ENV === 'production' ? 'warning' : false,
      maxEntrypointSize: 512000,
      maxAssetSize: 512000
    }
  },

  // Chain webpack configuration
  chainWebpack: config => {
    // Remove prefetch for non-critical routes
    config.plugins.delete('prefetch')

    // Optimize images
    config.module
      .rule('images')
      .test(/\.(png|jpe?g|gif|webp|svg)(\?.*)?$/)
      .use('url-loader')
      .loader('url-loader')
      .options({
        limit: 4096,
        fallback: {
          loader: 'file-loader',
          options: {
            name: 'img/[name].[hash:8].[ext]'
          }
        }
      })

    // Optimize fonts
    config.module
      .rule('fonts')
      .test(/\.(woff2?|eot|ttf|otf)(\?.*)?$/i)
      .use('url-loader')
      .loader('url-loader')
      .options({
        limit: 4096,
        fallback: {
          loader: 'file-loader',
          options: {
            name: 'fonts/[name].[hash:8].[ext]'
          }
        }
      })
  },

  // CSS configuration
  css: {
    loaderOptions: {
      sass: {
        additionalData: `
          @import "@/styles/variables.scss";
        `
      }
    },
    sourceMap: process.env.NODE_ENV !== 'production'
  },

  // Production source maps
  productionSourceMap: false,

  // Linting on save
  lintOnSave: process.env.NODE_ENV !== 'production',

  // Parallel builds
  parallel: require('os').cpus().length > 1,

  // Plugin options
  pluginOptions: {
    vuetify: {
      // Vuetify options
      theme: {
        dark: false,
        default: 'light',
        themes: {
          light: {
            primary: '#2E8B57',
            secondary: '#20B2AA',
            accent: '#FFD700',
            error: '#F44336',
            warning: '#FF9800',
            info: '#2196F3',
            success: '#4CAF50'
          }
        }
      }
    }
  }
})