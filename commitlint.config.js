module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [
      2,
      'always',
      [
        'feat',     // New feature
        'fix',      // Bug fix
        'docs',     // Documentation only
        'style',    // Formatting, missing semi colons, etc
        'refactor', // Code change that neither fixes nor adds
        'perf',     // Performance improvements
        'test',     // Adding missing tests
        'chore',    // Maintain, dependencies, etc
        'ci',       // CI/CD changes
        'build',    // Build system changes
        'revert',   // Revert a previous commit
      ],
    ],
    'scope-case': [2, 'always', 'kebab-case'],
    'subject-case': [0],  // Allow any case
    'subject-empty': [2, 'never'],
    'subject-full-stop': [2, 'never', '.'],
    'header-max-length': [2, 'always', 100],
    'body-leading-blank': [2, 'always'],
    'body-max-line-length': [0],  // Allow long lines in body
    'footer-leading-blank': [2, 'always'],
  },
};
