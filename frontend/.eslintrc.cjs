module.exports = {
  root: true,
  ignorePatterns: ['dist/', 'node_modules/'],
  parser: '@typescript-eslint/parser',
  parserOptions: { ecmaVersion: 2022, sourceType: 'module', ecmaFeatures: { jsx: true } },
  env: { browser: true, es2022: true, node: true },
  rules: {
    'no-console': 'warn',
    'no-unused-vars': 'off',
  },
}
