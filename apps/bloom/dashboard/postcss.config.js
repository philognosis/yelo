/**
 * PostCSS Configuration
 * Processes CSS with Tailwind and Autoprefixer
 */
module.exports = {
  plugins: {
    // Tailwind CSS
    tailwindcss: {},
    // Autoprefixer for browser compatibility
    autoprefixer: {},
    // CSS Nano for production optimization
    ...(process.env.NODE_ENV === 'production'
      ? {
          cssnano: {
            preset: [
              'default',
              {
                discardComments: {
                  removeAll: true,
                },
                normalizeWhitespace: true,
              },
            ],
          },
        }
      : {}),
  },
};
