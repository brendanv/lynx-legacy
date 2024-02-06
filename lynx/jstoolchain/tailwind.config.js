/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["../templates/**/*.html", "../views/**/*.py"],
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
  daisyui: {
    themes: ['emerald', 'dracula'],
    darkTheme: 'dracula'
  },
  safelist: [
    {
      pattern: /alert-(info|warning|error|success|debug)/
    },
    'checkbox-primary',
  ]
}

