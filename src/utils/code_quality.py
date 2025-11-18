"""Code quality analysis for agentic coding tracing."""

import ast
import logging
import re
import subprocess
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class QualityScore:
    """
    Comprehensive code quality score.

    Attributes:
        overall: Overall quality score (0-1)
        syntax_correctness: Syntax validity (0-1)
        style_compliance: Style guide compliance (0-1)
        complexity_score: Code complexity score (0-1, lower complexity = higher score)
        security_score: Security analysis score (0-1)
        breakdown: Detailed breakdown of each metric
        issues: List of identified issues
        suggestions: List of improvement suggestions
    """

    overall: float
    syntax_correctness: float
    style_compliance: float
    complexity_score: float
    security_score: float
    breakdown: Dict[str, Any]
    issues: List[Dict[str, str]]
    suggestions: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for tracing."""
        return {
            "overall": self.overall,
            "syntax_correctness": self.syntax_correctness,
            "style_compliance": self.style_compliance,
            "complexity_score": self.complexity_score,
            "security_score": self.security_score,
            "breakdown": self.breakdown,
            "num_issues": len(self.issues),
            "num_suggestions": len(self.suggestions),
        }

    def get_scores_dict(self) -> Dict[str, float]:
        """Get scores as a flat dictionary for LangFuse scoring."""
        return {
            "code_quality_overall": self.overall,
            "code_quality_syntax": self.syntax_correctness,
            "code_quality_style": self.style_compliance,
            "code_quality_complexity": self.complexity_score,
            "code_quality_security": self.security_score,
        }


class CodeQualityAnalyzer:
    """
    Comprehensive code quality analyzer.

    Supports multiple languages and provides detailed quality metrics:
    - Syntax correctness (via parsing)
    - Style compliance (basic checks)
    - Complexity analysis (cyclomatic complexity, nesting depth)
    - Security issues (common vulnerabilities)
    """

    # Language-specific configurations
    SUPPORTED_LANGUAGES = ["python", "javascript", "typescript", "java", "go", "rust"]

    # Weights for overall score calculation
    WEIGHTS = {
        "syntax_correctness": 0.30,
        "style_compliance": 0.20,
        "complexity_score": 0.25,
        "security_score": 0.25,
    }

    # Common security patterns to check
    SECURITY_PATTERNS = {
        "python": [
            (r"eval\s*\(", "Use of eval() is dangerous"),
            (r"exec\s*\(", "Use of exec() is dangerous"),
            (r"__import__\s*\(", "Dynamic imports can be dangerous"),
            (r"pickle\.loads?", "Pickle deserialization can be exploited"),
            (r"subprocess\.call.*shell\s*=\s*True", "Shell injection risk"),
            (r"os\.system\s*\(", "Command injection risk"),
            (r"sql.*%", "Potential SQL injection (use parameterized queries)"),
            (r"password\s*=\s*['\"]", "Hardcoded password detected"),
            (r"api[_-]?key\s*=\s*['\"]", "Hardcoded API key detected"),
        ],
        "javascript": [
            (r"eval\s*\(", "Use of eval() is dangerous"),
            (r"innerHTML\s*=", "XSS risk with innerHTML (use textContent)"),
            (r"document\.write", "document.write can enable XSS"),
            (r"dangerouslySetInnerHTML", "React XSS risk"),
            (r"child_process\.exec", "Command injection risk"),
            (r"password\s*[:=]\s*['\"]", "Hardcoded password detected"),
        ],
    }

    # Style checking patterns
    STYLE_PATTERNS = {
        "python": [
            (r"^import \*", "Avoid wildcard imports"),
            (r"\t", "Use spaces instead of tabs (PEP 8)"),
            (r"^class [a-z]", "Class names should be CamelCase"),
            (r"^def [A-Z]", "Function names should be snake_case"),
        ],
        "javascript": [
            (r"^var ", "Use let/const instead of var"),
            (r"==(?!=)", "Use === instead of =="),
            (r"!=(?!=)", "Use !== instead of !="),
        ],
    }

    def analyze(self, code: str, language: str = "python") -> QualityScore:
        """
        Perform comprehensive code quality analysis.

        Args:
            code: Source code to analyze
            language: Programming language

        Returns:
            QualityScore with detailed metrics
        """
        language = language.lower()

        if language not in self.SUPPORTED_LANGUAGES:
            logger.warning(f"Unsupported language: {language}, using basic analysis")
            return self._basic_analysis(code, language)

        # Perform language-specific analysis
        if language == "python":
            return self._analyze_python(code)
        elif language in ["javascript", "typescript"]:
            return self._analyze_javascript(code)
        else:
            return self._basic_analysis(code, language)

    def _analyze_python(self, code: str) -> QualityScore:
        """Analyze Python code quality."""
        issues = []
        suggestions = []
        breakdown = {}

        # 1. Syntax Correctness
        syntax_score, syntax_issues = self._check_python_syntax(code)
        issues.extend(syntax_issues)
        breakdown["syntax"] = {"score": syntax_score, "issues": len(syntax_issues)}

        # 2. Style Compliance
        style_score, style_issues = self._check_style(code, "python")
        issues.extend(style_issues)
        breakdown["style"] = {"score": style_score, "issues": len(style_issues)}

        # 3. Complexity Analysis
        complexity_score, complexity_metrics = self._analyze_complexity_python(code)
        breakdown["complexity"] = complexity_metrics

        # 4. Security Analysis
        security_score, security_issues = self._check_security(code, "python")
        issues.extend(security_issues)
        breakdown["security"] = {"score": security_score, "issues": len(security_issues)}

        # 5. Calculate Overall Score
        overall = (
            syntax_score * self.WEIGHTS["syntax_correctness"]
            + style_score * self.WEIGHTS["style_compliance"]
            + complexity_score * self.WEIGHTS["complexity_score"]
            + security_score * self.WEIGHTS["security_score"]
        )

        # Generate suggestions
        if syntax_score < 1.0:
            suggestions.append("Fix syntax errors before proceeding")
        if style_score < 0.7:
            suggestions.append("Run a linter (pylint, flake8) to improve code style")
        if complexity_score < 0.6:
            suggestions.append("Consider refactoring to reduce complexity")
        if security_score < 0.8:
            suggestions.append("Review and fix security issues")

        return QualityScore(
            overall=round(overall, 3),
            syntax_correctness=syntax_score,
            style_compliance=style_score,
            complexity_score=complexity_score,
            security_score=security_score,
            breakdown=breakdown,
            issues=issues,
            suggestions=suggestions,
        )

    def _check_python_syntax(self, code: str) -> Tuple[float, List[Dict[str, str]]]:
        """Check Python syntax correctness."""
        try:
            ast.parse(code)
            return 1.0, []
        except SyntaxError as e:
            issue = {
                "type": "syntax_error",
                "severity": "error",
                "message": str(e),
                "line": e.lineno if hasattr(e, "lineno") else None,
            }
            return 0.0, [issue]
        except Exception as e:
            issue = {
                "type": "parse_error",
                "severity": "error",
                "message": f"Failed to parse code: {e}",
            }
            return 0.0, [issue]

    def _analyze_complexity_python(self, code: str) -> Tuple[float, Dict[str, Any]]:
        """
        Analyze Python code complexity.

        Metrics:
        - Cyclomatic complexity (approximate via control flow keywords)
        - Nesting depth
        - Function length
        - Number of functions/classes
        """
        metrics = {
            "cyclomatic_complexity": 1,
            "max_nesting_depth": 0,
            "avg_function_length": 0,
            "num_functions": 0,
            "num_classes": 0,
        }

        try:
            tree = ast.parse(code)

            # Count functions and classes
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    metrics["num_functions"] += 1
                elif isinstance(node, ast.ClassDef):
                    metrics["num_classes"] += 1

                # Count decision points (if, for, while, etc.)
                if isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                    metrics["cyclomatic_complexity"] += 1

            # Calculate nesting depth
            metrics["max_nesting_depth"] = self._calculate_nesting_depth(tree)

            # Calculate average function length
            if metrics["num_functions"] > 0:
                total_lines = len(code.split("\n"))
                metrics["avg_function_length"] = total_lines // metrics["num_functions"]

        except Exception as e:
            logger.warning(f"Failed to analyze complexity: {e}")

        # Score based on complexity (lower is better)
        # Cyclomatic complexity: 1-10 = excellent, 11-20 = good, 21-50 = fair, 50+ = poor
        if metrics["cyclomatic_complexity"] <= 10:
            complexity_score = 1.0
        elif metrics["cyclomatic_complexity"] <= 20:
            complexity_score = 0.8
        elif metrics["cyclomatic_complexity"] <= 50:
            complexity_score = 0.6
        else:
            complexity_score = 0.4

        # Penalize deep nesting (>4 is bad)
        if metrics["max_nesting_depth"] > 4:
            complexity_score *= 0.8

        # Penalize very long functions (>50 lines)
        if metrics["avg_function_length"] > 50:
            complexity_score *= 0.9

        metrics["score"] = round(complexity_score, 3)
        return complexity_score, metrics

    def _calculate_nesting_depth(self, tree: ast.AST) -> int:
        """Calculate maximum nesting depth in AST."""
        max_depth = 0

        def visit_node(node: ast.AST, depth: int):
            nonlocal max_depth
            max_depth = max(max_depth, depth)

            # Control flow nodes increase nesting
            if isinstance(
                node, (ast.If, ast.For, ast.While, ast.With, ast.Try, ast.FunctionDef, ast.ClassDef)
            ):
                depth += 1

            for child in ast.iter_child_nodes(node):
                visit_node(child, depth)

        visit_node(tree, 0)
        return max_depth

    def _check_style(self, code: str, language: str) -> Tuple[float, List[Dict[str, str]]]:
        """Check code style compliance."""
        issues = []
        patterns = self.STYLE_PATTERNS.get(language, [])

        lines = code.split("\n")
        for line_num, line in enumerate(lines, 1):
            for pattern, message in patterns:
                if re.search(pattern, line):
                    issues.append(
                        {
                            "type": "style_violation",
                            "severity": "warning",
                            "message": message,
                            "line": line_num,
                        }
                    )

        # Calculate score (each issue reduces score)
        if len(lines) == 0:
            return 1.0, issues

        # Deduct 0.05 per issue, minimum 0.5
        score = max(0.5, 1.0 - (len(issues) * 0.05))
        return round(score, 3), issues

    def _check_security(self, code: str, language: str) -> Tuple[float, List[Dict[str, str]]]:
        """Check for common security issues."""
        issues = []
        patterns = self.SECURITY_PATTERNS.get(language, [])

        lines = code.split("\n")
        for line_num, line in enumerate(lines, 1):
            for pattern, message in patterns:
                if re.search(pattern, line):
                    issues.append(
                        {
                            "type": "security_issue",
                            "severity": "error" if "dangerous" in message.lower() else "warning",
                            "message": message,
                            "line": line_num,
                        }
                    )

        # Calculate score (security issues are more severe)
        if len(issues) == 0:
            return 1.0, issues

        # Each security issue is -0.15, minimum 0.3
        score = max(0.3, 1.0 - (len(issues) * 0.15))
        return round(score, 3), issues

    def _analyze_javascript(self, code: str) -> QualityScore:
        """Analyze JavaScript/TypeScript code quality."""
        issues = []
        suggestions = []
        breakdown = {}

        # Basic syntax check (simplified - would need proper JS parser)
        syntax_score, syntax_issues = self._check_javascript_syntax(code)
        issues.extend(syntax_issues)
        breakdown["syntax"] = {"score": syntax_score, "issues": len(syntax_issues)}

        # Style check
        style_score, style_issues = self._check_style(code, "javascript")
        issues.extend(style_issues)
        breakdown["style"] = {"score": style_score, "issues": len(style_issues)}

        # Simplified complexity (count control flow keywords)
        complexity_score = self._analyze_complexity_javascript(code)
        breakdown["complexity"] = {"score": complexity_score}

        # Security check
        security_score, security_issues = self._check_security(code, "javascript")
        issues.extend(security_issues)
        breakdown["security"] = {"score": security_score, "issues": len(security_issues)}

        # Overall score
        overall = (
            syntax_score * self.WEIGHTS["syntax_correctness"]
            + style_score * self.WEIGHTS["style_compliance"]
            + complexity_score * self.WEIGHTS["complexity_score"]
            + security_score * self.WEIGHTS["security_score"]
        )

        return QualityScore(
            overall=round(overall, 3),
            syntax_correctness=syntax_score,
            style_compliance=style_score,
            complexity_score=complexity_score,
            security_score=security_score,
            breakdown=breakdown,
            issues=issues,
            suggestions=suggestions,
        )

    def _check_javascript_syntax(self, code: str) -> Tuple[float, List[Dict[str, str]]]:
        """Basic JavaScript syntax check."""
        # Simplified check - look for common syntax errors
        issues = []

        # Check for unmatched braces
        open_braces = code.count("{")
        close_braces = code.count("}")
        if open_braces != close_braces:
            issues.append(
                {
                    "type": "syntax_error",
                    "severity": "error",
                    "message": f"Unmatched braces: {open_braces} {{ vs {close_braces} }}",
                }
            )

        # Check for unmatched parentheses
        open_parens = code.count("(")
        close_parens = code.count(")")
        if open_parens != close_parens:
            issues.append(
                {
                    "type": "syntax_error",
                    "severity": "error",
                    "message": f"Unmatched parentheses: {open_parens} ( vs {close_parens} )",
                }
            )

        score = 1.0 if len(issues) == 0 else 0.5
        return score, issues

    def _analyze_complexity_javascript(self, code: str) -> float:
        """Simplified JavaScript complexity analysis."""
        # Count control flow keywords
        keywords = ["if", "else", "for", "while", "switch", "case", "catch"]
        complexity = 1

        for keyword in keywords:
            complexity += len(re.findall(rf"\b{keyword}\b", code))

        # Score based on complexity
        if complexity <= 10:
            return 1.0
        elif complexity <= 20:
            return 0.8
        elif complexity <= 50:
            return 0.6
        else:
            return 0.4

    def _basic_analysis(self, code: str, language: str) -> QualityScore:
        """Basic analysis for unsupported languages."""
        # Very basic checks
        lines = code.split("\n")
        non_empty_lines = [line for line in lines if line.strip()]

        # Assume syntax is okay if code is not empty
        syntax_score = 1.0 if len(non_empty_lines) > 0 else 0.0

        # Basic length-based complexity
        complexity_score = 1.0 if len(non_empty_lines) < 50 else 0.8

        # Default scores
        style_score = 0.8
        security_score = 0.8

        overall = (
            syntax_score * self.WEIGHTS["syntax_correctness"]
            + style_score * self.WEIGHTS["style_compliance"]
            + complexity_score * self.WEIGHTS["complexity_score"]
            + security_score * self.WEIGHTS["security_score"]
        )

        return QualityScore(
            overall=round(overall, 3),
            syntax_correctness=syntax_score,
            style_compliance=style_score,
            complexity_score=complexity_score,
            security_score=security_score,
            breakdown={
                "message": f"Basic analysis only (language '{language}' not fully supported)"
            },
            issues=[],
            suggestions=[f"Add support for {language} for detailed analysis"],
        )


# Global analyzer instance
_code_quality_analyzer: Optional[CodeQualityAnalyzer] = None


def get_code_quality_analyzer() -> CodeQualityAnalyzer:
    """Get the global code quality analyzer instance."""
    global _code_quality_analyzer
    if _code_quality_analyzer is None:
        _code_quality_analyzer = CodeQualityAnalyzer()
    return _code_quality_analyzer
