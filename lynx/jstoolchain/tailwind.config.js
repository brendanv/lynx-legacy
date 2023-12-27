/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["../templates/**/*.html"],
  theme: {
    fontFamily: {
      figtree: ["Figtree"],
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
    require('@tailwindcss/forms'),
    require("daisyui")
  ],
  safelist: [
    {
      pattern: /alert-(info|warning|error|success|debug)/
    },
    'checkbox-primary',
  ]
}

