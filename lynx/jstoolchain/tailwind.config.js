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
    themes: [
      {
        "light": {
          ...require("daisyui/src/theming/themes")["cupcake"],
        }
      },
      {
        // Sunset, but switch two button colors, and round buttons like
        // the light theme.
        "dark": {
          ...require("daisyui/src/theming/themes")["sunset"],
          primary: require("daisyui/src/theming/themes")["sunset"]["accent"],
          accent: require("daisyui/src/theming/themes")["sunset"]["primary"],
          "--rounded-btn": require("daisyui/src/theming/themes")["cupcake"]["--rounded-btn"],
          "--rounded-box": require("daisyui/src/theming/themes")["cupcake"]["--rounded-box"],
          "--rounded-badge": require("daisyui/src/theming/themes")["cupcake"]["--rounded-badge"]
        }
      }
    ],
    darkTheme: 'dark'
  },
  safelist: [
    {
      pattern: /alert-(info|warning|error|success|debug)/
    },
    'checkbox-primary',
  ]
}

