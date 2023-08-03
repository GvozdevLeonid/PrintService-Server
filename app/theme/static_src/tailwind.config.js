/**
 * Tailwind config.
 **/

module.exports = {
    content: [
        /**
         * HTML. Paths to Django template files that will contain Tailwind CSS classes.
         **/

        /*
         * Main templates directory of the project (BASE_DIR/templates).
         */
        '../../templates/**/*.html',

        /*
         * Templates in other django apps (BASE_DIR/<any_app_name>/templates).
         **/
        '../../**/templates/**/*.html',

        /**
         * JS. Paths to JS files that will contain Tailwind CSS classes (BASE_DIR/static/static/js).
         **/
        '../../static/static/js/*.js',

    ],
    theme: {
        /**
         * Rewrite styles or add new ones.
         **/
        container: {
            center: true,
          },
        extend: {},
    },
    plugins: [
        require('@tailwindcss/forms'),
        require('@tailwindcss/typography'),
        require('@tailwindcss/line-clamp'),
        require('@tailwindcss/aspect-ratio'),
    ],
}
