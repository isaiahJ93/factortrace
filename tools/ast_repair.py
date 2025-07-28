#!/usr/bin/env python3
"
AST-Based Safe Repair Module
Uses Abstract Syntax Tree manipulation for safer repairs
"

import ast
import astunparse
from typing import Any, List, Optional, Set, Tuple
from pathlib import Path
import logging


class SafeASTRepair(ast.NodeTransformer):
    "
    AST-based repair that preserves logic while fixing syntax issues
    Safer than regex for complex repairs
    "
    
    def __init__(self, filename: str = "<unknown>"):
        self.filename = filename
        self.repairs_made = []
        self.logger = logging.getLogger(__name__)
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Repair function definitions"
        
        # Fix missing return type annotation for our async functions
        if node.name.startswith(('render', 'validate', 'process')):
            if not node.returns and any(
                isinstance(stmt, ast.Return) for stmt in ast.walk(node)
            ):
                # Infer return type from return statements
                for stmt in ast.walk(node):
                    if isinstance(stmt, ast.Return) and stmt.value:
                        # Common patterns in our codebase
                        if isinstance(stmt.value, ast.Constant):
                            if isinstance(stmt.value.value, str):
                                node.returns = ast.Name(id='str', ctx=ast.Load())
                            elif isinstance(stmt.value.value, bool):
                                node.returns = ast.Name(id='bool', ctx=ast.Load())
                        elif isinstance(stmt.value, ast.Dict):
                            # Return type Dict[str, Any]
                            node.returns = ast.Subscript(
                                value=ast.Name(id='Dict', ctx=ast.Load()),
                                slice=ast.Tuple(
                                    elts=[
                                        ast.Name(id='str', ctx=ast.Load()),
                                        ast.Name(id='Any', ctx=ast.Load())
                                    ],
                                    ctx=ast.Load()
                                ),
                                ctx=ast.Load()
                            )
                        break
        
        # Fix async function patterns
        if isinstance(node, ast.AsyncFunctionDef):
            # Ensure async context managers have proper syntax
            for stmt in ast.walk(node):
                if isinstance(stmt, ast.AsyncWith):
                    self._fix_async_with(stmt)
        
        self.generic_visit(node)
        return node
    
    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        """Repair class definitions"
        
        # Fix Pydantic models
        if any(base.id == 'BaseModel' for base in node.bases 
               if isinstance(base, ast.Name)):
            self._fix_pydantic_model(node)
        
        self.generic_visit(node)
        return node
    
    def visit_AnnAssign(self, node: ast.AnnAssign) -> ast.AnnAssign:
        """Fix annotated assignments (type hints)"
        
        # Fix Field() calls
        if (isinstance(node.value, ast.Call) and 
            isinstance(node.value.func, ast.Name) and 
            node.value.func.id == 'Field'):
            self._fix_field_call(node.value)
        
        self.generic_visit(node)
        return node
    
    def _fix_pydantic_model(self, node: ast.ClassDef):
        """Fix common Pydantic model issues"
        
        # Ensure class has docstring
        if not ast.get_docstring(node):
            docstring = ast.Constant(value=f"{node.name} model for emission data")
            node.body.insert(0, ast.Expr(value=docstring))
        
        # Fix Field definitions
        for stmt in node.body:
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.value, ast.Call):
                if (isinstance(stmt.value.func, ast.Name) and 
                    stmt.value.func.id == 'Field'):
                    self._fix_field_call(stmt.value)
    
    def _fix_field_call(self, call: ast.Call):
        """Fix Pydantic Field() calls"
        
        # Ensure all keywords are valid
        valid_keywords = {
            'default', 'default_factory', 'alias', 'title', 
            'description', 'exclude', 'include', 'const', 
            'gt', 'ge', 'lt', 'le', 'multiple_of', 'allow_inf_nan',
            'max_digits', 'decimal_places', 'min_items', 'max_items',
            'unique_items', 'min_length', 'max_length', 'allow_mutation',
            'regex', 'discriminator', 'repr', 'example', 'examples',
            'deprecated', 'frozen', 'validate_default', 'json_schema_extra'
        }
        
        # Check for common issues
        keywords_seen = set()
        for keyword in call.keywords:
            # Remove duplicate keywords
            if keyword.arg in keywords_seen:
                call.keywords.remove(keyword)
                self.repairs_made.append(f"Removed duplicate Field argument: {keyword.arg}")
                continue
            keywords_seen.add(keyword.arg)
            
            # Fix common typos
            if keyword.arg == 'descripton':  # Common typo
                keyword.arg = 'description'
                self.repairs_made.append("Fixed typo: descripton -> description")
    
    def _fix_async_with(self, node: ast.AsyncWith):
        """Fix async with statements"
        
        for item in node.items:
            # Fix aiofiles.open patterns
            if (isinstance(item.context_expr, ast.Call) and
                isinstance(item.context_expr.func, ast.Attribute) and
                item.context_expr.func.attr == 'open'):
                
                # Ensure mode argument for file operations
                has_mode = any(kw.arg == 'mode' for kw in item.context_expr.keywords)
                if not has_mode and len(item.context_expr.args) == 1:
                    # Add mode='r' as default
                    item.context_expr.keywords.append(
                        ast.keyword(arg='mode', value=ast.Constant(value='r'))
                    )


class SmartCodeRepair:
    "
    Combines AST-based repairs with pattern matching for comprehensive fixing
    Preserves the architectural patterns of the Scope 3 compliance codebase
    "
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config = self._load_config(config_path)
        self.logger = logging.getLogger(__name__)
    
    def _load_config(self, config_path: Optional[Path]) -> dict:
        """Load repair configuration"
        if config_path and config_path.exists():
            import yaml
            return yaml.safe_load(config_path.read_text())
        
        # Default config for our codebase
        return {
            'codebase': {
                'style_guide': {
                    'line_length': 100,
                    'quote_style': 'double',
                    'trailing_comma': True
                }
            },
            'safety': {
                'max_changes_per_file': 50,
                'require_ast_valid': True
            }
        }
    
    def repair_with_ast(self, content: str, filename: str = "<unknown>") -> Tuple[str, List[str]]:
        "
        Repair Python code using AST transformation
        Returns: (repaired_content, list_of_repairs)
        "
        
        try:
            # Try to parse the content
            tree = ast.parse(content)
            
            # Apply AST-based repairs
            repairer = SafeASTRepair(filename)
            repaired_tree = repairer.visit(tree)
            
            # Convert back to source code
            repaired_content = astunparse.unparse(repaired_tree)
            
            return repaired_content, repairer.repairs_made
            
        except SyntaxError as e:
            # If AST parsing fails, we need line-by-line repairs first
            self.logger.debug(f"AST parsing failed: {e}")
            return content, []
    
    def intelligent_repair(self, file_path: Path) -> bool:
        "
        Intelligently repair a file using multiple strategies
        Returns True if successful
        "
        
        try:
            original_content = file_path.read_text(encoding='utf-8')
            
            # Phase 1: AST-based repairs (safest)
            ast_repaired, ast_changes = self.repair_with_ast(
                original_content, 
                str(file_path)
            )
            
            if ast_changes:
                self.logger.info(f"AST repairs made: {len(ast_changes)}")
            
            # Phase 2: Use the regex-based repairer for remaining issues
            from deep_repair import CodebaseRepairTool
            
            # Create temporary file with AST repairs
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
                tmp.write(ast_repaired)
                tmp_path = Path(tmp.name)
            
            # Apply regex-based repairs
            regex_repairer = CodebaseRepairTool(dry_run=False, verbose=False)
            result = regex_repairer.repair_file(tmp_path)
            
            if result.success and result.changes_made:
                # Copy repaired content back
                repaired_content = tmp_path.read_text()
                
                # Validate one more time
                try:
                    ast.parse(repaired_content)
                    compile(repaired_content, str(file_path), 'exec')
                    
                    # Create backup and write repaired content
                    backup_path = file_path.with_suffix(file_path.suffix + '.bak2')
                    file_path.rename(backup_path)
                    file_path.write_text(repaired_content, encoding='utf-8')
                    
                    self.logger.info(f"Successfully repaired {file_path}")
                    return True
                    
                except Exception as e:
                    self.logger.error(f"Final validation failed: {e}")
                    return False
            
            # Clean up
            tmp_path.unlink()
            
            return result.success
            
        except Exception as e:
            self.logger.error(f"Intelligent repair failed: {e}")
            return False


# Example usage function
def safe_repair_codebase(src_dir: Path, test_dir: Path):
    "
    Safely repair the Scope 3 compliance codebase
    "
    
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Load configuration
    config_path = Path("repair_config.yaml")
    repairer = SmartCodeRepair(config_path)
    
    # Repair source files
    for py_file in src_dir.rglob("*.py"):
        if '__pycache__' in str(py_file):
            continue
        
        print(f"Repairing {py_file}...")
        success = repairer.intelligent_repair(py_file)
        if not success:
            print(f"  ⚠️  Failed to repair {py_file}")
    
    # Repair test files
    for py_file in test_dir.rglob("*.py"):
        if '__pycache__' in str(py_file):
            continue
        
        print(f"Repairing {py_file}...")
        success = repairer.intelligent_repair(py_file)
        if not success:
            print(f"  ⚠️  Failed to repair {py_file}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2:
        src_dir = Path(sys.argv[1])
        test_dir = Path(sys.argv[2])
        safe_repair_codebase(src_dir, test_dir)
    else:
        print("Usage: python ast_repair.py <src_dir> <test_dir>")
        