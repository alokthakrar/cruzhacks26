"""
Symbolic math validator using SymPy (no AI needed).
Validates algebraic steps by checking if expressions are mathematically equivalent.
"""

from sympy import sympify, simplify, Eq, solve, symbols
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
from typing import List, Dict, Optional


class SymbolicValidator:
    """Validates math steps using symbolic computation (SymPy)."""
    
    def __init__(self):
        self.transformations = (standard_transformations + (implicit_multiplication_application,))
    
    def parse_expression(self, expr_str: str, preserve_plusminus: bool = False):
        """
        Parse a math expression string into SymPy format.
        Handles equations like "2x+5=13" and expressions like "2x+5".
        
        Args:
            preserve_plusminus: If True, don't convert ± to + (for validation purposes)
        """
        try:
            # Clean up the string
            expr_str = expr_str.strip()
            
            # Remove question numbers like "5) " or "1. " from the beginning
            import re
            expr_str = re.sub(r'^\d+[\.\)]\s*', '', expr_str)
            
            # Convert LaTeX \frac{a}{b} to (a)/(b) BEFORE removing spaces
            expr_str = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'((\1)/((\2)))', expr_str)
            
            # Convert LaTeX square root √ or \sqrt BEFORE other processing
            expr_str = expr_str.replace('√', 'sqrt')
            expr_str = re.sub(r'\\sqrt\{([^}]+)\}', r'sqrt(\1)', expr_str)
            expr_str = re.sub(r'\\sqrt\(([^)]+)\)', r'sqrt(\1)', expr_str)
            
            # Convert Unicode minus sign (−) and en-dash (–) to regular hyphen (-)
            expr_str = expr_str.replace('−', '-')
            expr_str = expr_str.replace('–', '-')  # en-dash
            expr_str = expr_str.replace('—', '-')  # em-dash
            
            # Handle ± and +/- symbols (only convert if not preserving it)
            if not preserve_plusminus:
                expr_str = expr_str.replace('±', '+')
                expr_str = expr_str.replace('+/-', '+')
                expr_str = expr_str.replace('-/+', '+')
            
            # Convert Unicode superscripts to regular notation
            superscript_map = {
                '⁰': '**0', '¹': '**1', '²': '**2', '³': '**3', 
                '⁴': '**4', '⁵': '**5', '⁶': '**6', '⁷': '**7', 
                '⁸': '**8', '⁹': '**9'
            }
            for sup, normal in superscript_map.items():
                expr_str = expr_str.replace(sup, normal)
            
            # Remove all spaces
            expr_str = expr_str.replace(' ', '')
            
            # Convert to lowercase for consistent variable names (x vs X)
            expr_str = expr_str.lower()
            
            # Convert ^ to ** for exponentiation
            expr_str = expr_str.replace('^', '**')
            
            # Check if it's an equation (contains =)
            if '=' in expr_str:
                left, right = expr_str.split('=', 1)
                
                # Handle multiple solutions like "x=-3,-4" 
                if ',' in right:
                    # This is a final answer with multiple solutions
                    # Just return as a simple equation for now (validation will handle it specially)
                    pass
                
                left_expr = parse_expr(left, transformations=self.transformations)
                right_expr = parse_expr(right, transformations=self.transformations)
                return Eq(left_expr, right_expr)
            else:
                # Just an expression
                return parse_expr(expr_str, transformations=self.transformations)
        except Exception as e:
            raise ValueError(f"Could not parse '{expr_str}': {str(e)}")
    
    def detect_operation(self, prev: Eq, curr: Eq) -> Optional[str]:
        """
        Detect what algebraic operation was applied between two equations.
        Returns a string describing the operation or None if unclear.
        """
        try:
            # Check for addition/subtraction on both sides
            diff_left = simplify(curr.lhs - prev.lhs)
            diff_right = simplify(curr.rhs - prev.rhs)
            
            if simplify(diff_left - diff_right) == 0 and diff_left != 0:
                if diff_left > 0:
                    return f"added {diff_left} to both sides"
                else:
                    return f"subtracted {abs(diff_left)} from both sides"
            
            # Check for multiplication/division on both sides
            if prev.lhs != 0 and curr.lhs != 0:
                ratio_left = simplify(curr.lhs / prev.lhs)
                ratio_right = simplify(curr.rhs / prev.rhs)
                
                if simplify(ratio_left - ratio_right) == 0 and ratio_left != 1:
                    if ratio_left > 1:
                        return f"multiplied both sides by {ratio_left}"
                    else:
                        return f"divided both sides by {simplify(1/ratio_left)}"
            
            # Check if it's just simplification (same solution, different form)
            return "simplified"
            
        except:
            return None
    
    def is_simpler(self, prev: Eq, curr: Eq) -> bool:
        """Check if curr is simpler/more progressed than prev."""
        try:
            # Check if we're isolating the variable (fewer terms with variable)
            prev_lhs_has_var = any(str(s) in 'xyzabc' for s in prev.lhs.free_symbols)
            curr_lhs_has_var = any(str(s) in 'xyzabc' for s in curr.lhs.free_symbols)
            
            # Progress if we isolated variable to one side
            if prev_lhs_has_var and not curr_lhs_has_var:
                return True
            if not prev_lhs_has_var and curr_lhs_has_var:
                return True
            
            # Expanding is also progress (removes parentheses)
            if '(' in str(prev) and '(' not in str(curr):
                return True
            
            # Count terms and complexity (fallback to length check)
            prev_terms = len(str(prev.lhs)) + len(str(prev.rhs))
            curr_terms = len(str(curr.lhs)) + len(str(curr.rhs))
            
            # Simpler if fewer characters (with some tolerance)
            return curr_terms <= prev_terms + 3
        except:
            return False
    
    def validate_step(self, prev_expr: str, curr_expr: str) -> Dict:
        """
        Check if curr_expr is a valid algebraic step from prev_expr.
        
        Returns:
            {
                "is_valid": bool,
                "error": str or None,
                "explanation": str,
                "warning": str or None
            }
        """
        try:
            # Special handling for ± notation (e.g., "x=(-4±2)/(2)") or +/- (ASCII version)
            has_plusminus = ('±' in curr_expr or '+/-' in curr_expr or '-/+' in curr_expr) and '=' in curr_expr
            if has_plusminus:
                # Validate both the + and - versions
                try:
                    # If previous expression ALSO has ±, we need to parse it properly too
                    has_prev_plusminus = '±' in prev_expr or '+/-' in prev_expr or '-/+' in prev_expr
                    if has_prev_plusminus:
                        # Parse both versions of previous expression
                        prev_plus = prev_expr.replace('±', '+').replace('+/-', '+').replace('-/+', '+')
                        prev_minus = prev_expr.replace('±', '-').replace('+/-', '-').replace('-/+', '-')
                        prev_plus_parsed = self.parse_expression(prev_plus)
                        prev_minus_parsed = self.parse_expression(prev_minus)
                        
                        # Get all solutions from both versions
                        prev_vals = set()
                        if isinstance(prev_plus_parsed, Eq):
                            for sol_dict in solve(prev_plus_parsed, dict=True):
                                for var, val in sol_dict.items():
                                    prev_vals.add(str(simplify(val)))
                        if isinstance(prev_minus_parsed, Eq):
                            for sol_dict in solve(prev_minus_parsed, dict=True):
                                for var, val in sol_dict.items():
                                    prev_vals.add(str(simplify(val)))
                    else:
                        # Previous expression doesn't have ±, parse normally
                        prev = self.parse_expression(prev_expr)
                        prev_vals = set()
                        if isinstance(prev, Eq):
                            prev_solutions = solve(prev, dict=True)
                            for sol_dict in prev_solutions:
                                for var, val in sol_dict.items():
                                    prev_vals.add(str(simplify(val)))
                    
                    # Parse with + and with -
                    curr_plus = curr_expr.replace('±', '+').replace('+/-', '+').replace('-/+', '+')
                    curr_minus = curr_expr.replace('±', '-').replace('+/-', '-').replace('-/+', '-')
                    
                    curr_plus_parsed = self.parse_expression(curr_plus)
                    curr_minus_parsed = self.parse_expression(curr_minus)
                    
                    # Get solution values from + and - versions of current
                    curr_vals = set()
                    if isinstance(curr_plus_parsed, Eq):
                        plus_solutions = solve(curr_plus_parsed, dict=True)
                        for sol_dict in plus_solutions:
                            for var, val in sol_dict.items():
                                curr_vals.add(str(simplify(val)))
                    if isinstance(curr_minus_parsed, Eq):
                        minus_solutions = solve(curr_minus_parsed, dict=True)
                        for sol_dict in minus_solutions:
                            for var, val in sol_dict.items():
                                curr_vals.add(str(simplify(val)))
                    
                    # Check if the ± notation covers all solutions
                    if curr_vals == prev_vals:
                        return {
                            "is_valid": True,
                            "error": None,
                            "explanation": "Valid algebraic step",
                            "warning": None
                        }
                    else:
                        return {
                            "is_valid": False,
                            "error": f"Solutions don't match: got {curr_vals}, expected {prev_vals}",
                            "explanation": "Check your arithmetic",
                            "warning": None
                        }
                except Exception as e:
                    print(f"DEBUG: ± validation error: {e}")
                    # Fall through to normal validation
                    pass
            
            # Check for final answer format like "x=-3,-4" (multiple solutions)
            if '=' in curr_expr and ',' in curr_expr.split('=')[1]:
                # This is a final answer with multiple solutions
                # Solve the previous equation and check if these are the correct solutions
                
                # Extract the solutions from curr_expr (e.g., "x=-3,-4")
                curr_expr_clean = curr_expr.strip()
                # Remove question numbers
                import re
                curr_expr_clean = re.sub(r'^\d+[\.\)]\s*', '', curr_expr_clean)
                curr_expr_clean = curr_expr_clean.replace(' ', '')
                
                var_part, solutions_part = curr_expr_clean.split('=', 1)
                var_name = var_part.strip().lower()
                solution_values = [s.strip() for s in solutions_part.split(',')]
                print(f"DEBUG: Extracted var_name: {var_name}, solution_values: {solution_values}")
                
                # Get expected solutions from previous expression
                expected_values = []
                var_symbol = symbols(var_name)
                
                # If previous expression has ± or +/-, handle it specially
                has_prev_plusminus = '±' in prev_expr or '+/-' in prev_expr or '-/+' in prev_expr
                if has_prev_plusminus:
                    prev_plus = prev_expr.replace('±', '+').replace('+/-', '+').replace('-/+', '+')
                    prev_minus = prev_expr.replace('±', '-').replace('+/-', '-').replace('-/+', '-')
                    prev_plus_parsed = self.parse_expression(prev_plus)
                    prev_minus_parsed = self.parse_expression(prev_minus)
                    
                    # Get all solutions from both versions
                    if isinstance(prev_plus_parsed, Eq):
                        for sol_dict in solve(prev_plus_parsed, dict=True):
                            if var_symbol in sol_dict:
                                expected_values.append(str(simplify(sol_dict[var_symbol])))
                    if isinstance(prev_minus_parsed, Eq):
                        for sol_dict in solve(prev_minus_parsed, dict=True):
                            if var_symbol in sol_dict:
                                expected_values.append(str(simplify(sol_dict[var_symbol])))
                else:
                    prev = self.parse_expression(prev_expr)
                    if isinstance(prev, Eq):
                        try:
                            prev_solutions = solve(prev, dict=True)
                            print(f"DEBUG: Solved prev equation: {prev}")
                            print(f"DEBUG: prev_solutions: {prev_solutions}")
                            
                            for sol in prev_solutions:
                                if var_symbol in sol:
                                    val = sol[var_symbol]
                                    # Convert to string and simplify rational numbers
                                    expected_values.append(str(simplify(val)))
                        except Exception as e:
                            print(f"DEBUG: Error solving prev: {e}")
                
                print(f"DEBUG: expected_values: {expected_values}")
                
                # If no expected values found, return error
                if not expected_values:
                    return {
                        "is_valid": False,
                        "error": "Could not extract expected solutions from previous step",
                        "explanation": "Check the format of your answer",
                        "warning": None
                    }
                
                # Sort both for comparison
                solution_values_sorted = sorted(solution_values)
                expected_values_sorted = sorted(expected_values)
                
                if solution_values_sorted == expected_values_sorted:
                    return {
                        "is_valid": True,
                        "error": None,
                        "explanation": "Correct final answer!",
                        "warning": None
                    }
                else:
                    expected_str = ', '.join(expected_values_sorted) if expected_values_sorted else 'unknown'
                    return {
                        "is_valid": False,
                        "error": f"Incorrect solutions: got [{', '.join(solution_values_sorted)}], expected [{expected_str}]",
                        "explanation": "Double-check your calculation",
                        "warning": None
                    }
            
            prev = self.parse_expression(prev_expr)
            curr = self.parse_expression(curr_expr)
            
            # If both are equations, check if they have the same solution set
            if isinstance(prev, Eq) and isinstance(curr, Eq):
                # Try to solve both equations and compare solutions
                try:
                    prev_solutions = solve(prev, dict=True)
                    curr_solutions = solve(curr, dict=True)
                    
                    # Check if solution sets are equal
                    if prev_solutions == curr_solutions or \
                       (len(prev_solutions) == 1 and len(curr_solutions) == 1 and 
                        all(simplify(prev_solutions[0][k] - curr_solutions[0][k]) == 0 
                            for k in prev_solutions[0].keys() if k in curr_solutions[0])):
                        
                        # Valid step - detect what operation was used
                        operation = self.detect_operation(prev, curr)
                        is_progress = self.is_simpler(prev, curr)
                        
                        warning = None
                        if not is_progress:
                            # Show warning for any step that doesn't make progress
                            if operation and operation != "simplified":
                                warning = f"Valid, but this makes the equation more complex ({operation})"
                            else:
                                warning = "Valid, but you could simplify further"
                        
                        explanation = "Valid algebraic step"
                        if operation:
                            explanation += f" ({operation})"
                        
                        return {
                            "is_valid": True,
                            "error": None,
                            "explanation": explanation,
                            "warning": warning
                        }
                    else:
                        # Get the actual solutions for better error message
                        prev_sol_str = ", ".join([f"{k}={v}" for sol in prev_solutions for k, v in sol.items()]) if prev_solutions else "no solution"
                        curr_sol_str = ", ".join([f"{k}={v}" for sol in curr_solutions for k, v in sol.items()]) if curr_solutions else "no solution"
                        
                        operation = self.detect_operation(prev, curr)
                        error_msg = "Incorrect transformation"
                        if operation:
                            error_msg += f" (attempted: {operation})"
                        error_msg += f": gives {curr_sol_str}, but should give {prev_sol_str}"
                        
                        return {
                            "is_valid": False,
                            "error": error_msg,
                            "explanation": "Double-check your arithmetic",
                            "warning": None
                        }
                except:
                    # If solve fails, fall back to checking equivalence
                    prev_diff = simplify(prev.lhs - prev.rhs)
                    curr_diff = simplify(curr.lhs - curr.rhs)
                    
                    if simplify(prev_diff - curr_diff) == 0:
                        return {
                            "is_valid": True,
                            "error": None,
                            "explanation": "Valid algebraic step",
                            "warning": None
                        }
                
                return {
                    "is_valid": False,
                    "error": "This step doesn't follow from the previous equation",
                    "explanation": "Check if you applied operations to both sides correctly",
                    "warning": None
                }
            else:
                # For non-equation expressions, check if they simplify to the same thing
                if simplify(prev - curr) == 0:
                    return {
                        "is_valid": True,
                        "error": None,
                        "explanation": "Expressions are equivalent",
                        "warning": None
                    }
                else:
                    return {
                        "is_valid": False,
                        "error": "These expressions don't have the same value",
                        "explanation": "Verify your simplification",
                        "warning": None
                    }
                    
        except ValueError as e:
            return {
                "is_valid": False,
                "error": str(e),
                "explanation": "Could not parse expression"
            }
        except Exception as e:
            return {
                "is_valid": False,
                "error": f"Validation error: {str(e)}",
                "explanation": "Unexpected error during validation"
            }
    
    def validate_sequence(self, expressions: List[str]) -> List[Dict]:
        """
        Validate a sequence of math steps.
        
        Returns list of validation results, one for each step transition.
        Result at index i validates the step from expressions[i] to expressions[i+1].
        """
        if len(expressions) < 2:
            return []
        
        results = []
        for i in range(len(expressions) - 1):
            result = self.validate_step(expressions[i], expressions[i + 1])
            result["step_number"] = i + 1
            result["from_expr"] = expressions[i]
            result["to_expr"] = expressions[i + 1]
            
            # Check if this is a final answer (e.g., x=3, y=-5, etc.)
            to_expr = expressions[i + 1].strip()
            import re
            # Match patterns like: x=3, y=-5, x=-3, n=42
            # Also match multiple solutions: x=-3,-4 or x=1,2,3
            final_answer_pattern = r'^[a-z]=-?\d+(?:,-?\d+)*$'
            is_final = bool(re.match(final_answer_pattern, to_expr.replace(' ', '')))
            result["is_final_answer"] = is_final
            
            results.append(result)
        
        return results


# Singleton instance
_validator_instance = None

def get_validator() -> SymbolicValidator:
    """Get the singleton validator instance."""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = SymbolicValidator()
    return _validator_instance
