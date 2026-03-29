export function getGradeClass(grade: string): string {
  return `grade-${grade.toLowerCase()}`;
}

export function getSeverityClass(severity: string): string {
  return `severity-${severity.toLowerCase()}`;
}

export function getGradeColor(grade: string): string {
  const colors: Record<string, string> = {
    AAA: '#059669', AA: '#10b981', A: '#34d399',
    BBB: '#a3e635', BB: '#facc15', B: '#fb923c',
    CCC: '#f97316', CC: '#ef4444', C: '#dc2626', D: '#991b1b',
  };
  return colors[grade] || '#6b7280';
}

export function getSeverityColor(severity: string): string {
  const colors: Record<string, string> = {
    critical: '#991b1b', high: '#ef4444',
    medium: '#f97316', low: '#facc15',
  };
  return colors[severity] || '#6b7280';
}

export function formatNumber(n: number): string {
  return new Intl.NumberFormat('pt-BR').format(n);
}

export function formatCurrency(n: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency', currency: 'USD',
  }).format(n);
}

export function formatScore(score: number): string {
  return score.toFixed(1);
}

export function getScoreColor(score: number): string {
  if (score >= 80) return '#059669';
  if (score >= 60) return '#10b981';
  if (score >= 40) return '#f59e0b';
  if (score >= 20) return '#f97316';
  return '#ef4444';
}
