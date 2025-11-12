"""
Code Tools for parsing and converting Camel routes
"""

import os
import re
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import javalang


def parse_xml_routes(xml_file_path: str) -> Dict[str, Any]:
    """
    Parse Camel XML DSL routes from a file.
    
    Args:
        xml_file_path: Path to the XML file containing Camel routes
        
    Returns:
        Dictionary with parsed route information
    """
    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        
        # Handle different XML namespaces
        namespaces = {
            'camel': 'http://camel.apache.org/schema/spring',
            'spring': 'http://www.springframework.org/schema/beans'
        }
        
        routes = []
        
        # Find all route elements
        route_elements = root.findall('.//camel:route', namespaces) or root.findall('.//route')
        
        for route_elem in route_elements:
            route_info = {
                'id': route_elem.get('id', 'unnamed'),
                'elements': []
            }
            
            # Parse route elements
            for child in route_elem:
                element_type = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                element_info = {
                    'type': element_type,
                    'attributes': dict(child.attrib),
                    'children': []
                }
                
                # Handle nested elements (like choice/when/otherwise)
                if element_type in ['choice', 'multicast', 'split', 'aggregate']:
                    for nested in child:
                        nested_type = nested.tag.split('}')[-1] if '}' in nested.tag else nested.tag
                        nested_info = {
                            'type': nested_type,
                            'attributes': dict(nested.attrib),
                            'elements': []
                        }
                        for nested_child in nested:
                            nested_child_type = nested_child.tag.split('}')[-1] if '}' in nested_child.tag else nested_child.tag
                            nested_info['elements'].append({
                                'type': nested_child_type,
                                'attributes': dict(nested_child.attrib)
                            })
                        element_info['children'].append(nested_info)
                
                route_info['elements'].append(element_info)
            
            routes.append(route_info)
        
        return {
            'status': 'Success',
            'file_path': xml_file_path,
            'routes': routes,
            'route_count': len(routes),
            'message': f'Successfully parsed {len(routes)} routes from XML'
        }
        
    except Exception as e:
        return {
            'status': 'Failure',
            'error': str(e),
            'message': f'Failed to parse XML routes: {str(e)}'
        }


def convert_xml_to_java_dsl(xml_routes: Dict[str, Any], package_name: str = "com.example.routes") -> str:
    """
    Convert parsed XML routes to Java DSL.
    
    Args:
        xml_routes: Parsed XML routes from parse_xml_routes
        package_name: Java package name for the generated class
        
    Returns:
        Generated Java DSL code as string
    """
    try:
        routes = xml_routes.get('routes', [])
        
        # Generate Java class
        java_code = []
        java_code.append(f"package {package_name};")
        java_code.append("")
        java_code.append("import org.apache.camel.builder.RouteBuilder;")
        java_code.append("import org.springframework.stereotype.Component;")
        java_code.append("")
        java_code.append("@Component")
        java_code.append("public class MigratedRoutes extends RouteBuilder {")
        java_code.append("")
        java_code.append("    @Override")
        java_code.append("    public void configure() throws Exception {")
        java_code.append("")
        
        for route in routes:
            route_id = route.get('id', 'unnamed')
            java_code.append(f"        // Route: {route_id}")
            
            route_builder = []
            
            for element in route.get('elements', []):
                element_type = element['type']
                attributes = element['attributes']
                
                if element_type == 'from':
                    uri = attributes.get('uri', '')
                    route_builder.append(f'from("{uri}")')
                    if route_id != 'unnamed':
                        route_builder.append(f'.routeId("{route_id}")')
                
                elif element_type == 'to':
                    uri = attributes.get('uri', '')
                    route_builder.append(f'.to("{uri}")')
                
                elif element_type == 'log':
                    message = attributes.get('message', '${body}')
                    route_builder.append(f'.log("{message}")')
                
                elif element_type == 'setBody':
                    simple = attributes.get('simple')
                    if simple:
                        route_builder.append(f'.setBody(simple("{simple}"))')
                    else:
                        route_builder.append('.setBody(exchange -> exchange.getIn().getBody())')
                
                elif element_type == 'setHeader':
                    header_name = attributes.get('name', 'header')
                    value = attributes.get('value') or attributes.get('simple')
                    if value:
                        route_builder.append(f'.setHeader("{header_name}", constant("{value}"))')
                
                elif element_type == 'choice':
                    route_builder.append('.choice()')
                    
                    for child in element.get('children', []):
                        if child['type'] == 'when':
                            condition = child['attributes'].get('simple', 'true')
                            route_builder.append(f'    .when(simple("{condition}"))')
                            
                            for when_element in child.get('elements', []):
                                if when_element['type'] == 'to':
                                    uri = when_element['attributes'].get('uri', '')
                                    route_builder.append(f'        .to("{uri}")')
                                elif when_element['type'] == 'log':
                                    message = when_element['attributes'].get('message', '')
                                    route_builder.append(f'        .log("{message}")')
                        
                        elif child['type'] == 'otherwise':
                            route_builder.append('    .otherwise()')
                            
                            for otherwise_element in child.get('elements', []):
                                if otherwise_element['type'] == 'to':
                                    uri = otherwise_element['attributes'].get('uri', '')
                                    route_builder.append(f'        .to("{uri}")')
                                elif otherwise_element['type'] == 'log':
                                    message = otherwise_element['attributes'].get('message', '')
                                    route_builder.append(f'        .log("{message}")')
                    
                    route_builder.append('    .end()')
                
                elif element_type == 'process':
                    ref = attributes.get('ref', 'processor')
                    route_builder.append(f'.process("{ref}")')
                
                elif element_type == 'bean':
                    ref = attributes.get('ref', 'bean')
                    method = attributes.get('method')
                    if method:
                        route_builder.append(f'.bean("{ref}", "{method}")')
                    else:
                        route_builder.append(f'.bean("{ref}")')
                
                elif element_type == 'transform':
                    simple = attributes.get('simple')
                    if simple:
                        route_builder.append(f'.transform(simple("{simple}"))')
                    else:
                        route_builder.append('.transform(exchange -> exchange.getMessage().getBody())')
                
                elif element_type == 'filter':
                    simple = attributes.get('simple', 'true')
                    route_builder.append(f'.filter(simple("{simple}"))')
                
                elif element_type == 'split':
                    simple = attributes.get('simple')
                    if simple:
                        route_builder.append(f'.split(simple("{simple}"))')
                    else:
                        route_builder.append('.split(body())')
                
                elif element_type == 'aggregate':
                    correlation = attributes.get('correlationExpression', 'header("id")')
                    route_builder.append(f'.aggregate({correlation})')
                    completion_size = attributes.get('completionSize')
                    if completion_size:
                        route_builder.append(f'.completionSize({completion_size})')
            
            # Join the route builder statements
            if route_builder:
                java_code.append("        " + "\n            ".join(route_builder) + ";")
                java_code.append("")
        
        java_code.append("    }")
        java_code.append("}")
        
        return '\n'.join(java_code)
        
    except Exception as e:
        return f"// Error converting XML to Java DSL: {str(e)}"


def refactor_java_code(java_file_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Refactor Java code from Camel 2 to Camel 4.
    
    Args:
        java_file_path: Path to the Java file to refactor
        output_path: Optional output path (defaults to overwriting input)
        
    Returns:
        Dictionary with refactoring results
    """
    try:
        with open(java_file_path, 'r') as f:
            original_code = f.read()
        
        refactored_code = original_code
        changes = []
        
        # Update imports
        import_mappings = {
            'org.apache.camel.Processor': 'org.apache.camel.Processor',
            'org.apache.camel.Exchange': 'org.apache.camel.Exchange',
            'org.apache.camel.Message': 'org.apache.camel.Message',
            'org.apache.camel.ProducerTemplate': 'org.apache.camel.ProducerTemplate',
            'org.apache.camel.ConsumerTemplate': 'org.apache.camel.ConsumerTemplate',
            'org.apache.camel.component.': 'org.apache.camel.component.',
            'org.apache.camel.impl.DefaultCamelContext': 'org.apache.camel.impl.engine.DefaultCamelContext',
            'org.apache.camel.impl.SimpleRegistry': 'org.apache.camel.support.SimpleRegistry',
            'org.apache.camel.impl.': 'org.apache.camel.support.',
        }
        
        for old_import, new_import in import_mappings.items():
            if old_import in refactored_code and old_import != new_import:
                refactored_code = refactored_code.replace(old_import, new_import)
                changes.append(f"Updated import: {old_import} -> {new_import}")
        
        # Update Exchange API usage
        # Replace getIn() with getMessage()
        if 'exchange.getIn()' in refactored_code:
            refactored_code = refactored_code.replace('exchange.getIn()', 'exchange.getMessage()')
            changes.append("Replaced exchange.getIn() with exchange.getMessage()")
        
        # Replace getOut() with getMessage()
        if 'exchange.getOut()' in refactored_code:
            refactored_code = refactored_code.replace('exchange.getOut()', 'exchange.getMessage()')
            changes.append("Replaced exchange.getOut() with exchange.getMessage()")
        
        # Update deprecated methods
        deprecated_patterns = [
            (r'exchange\.setOut\((.*?)\)', r'exchange.getMessage().setBody(\1)'),
            (r'exchange\.hasOut\(\)', r'exchange.hasMessage()'),
            (r'ProducerTemplate\.send\((.*?), exchange\)', r'ProducerTemplate.send(\1, exchange)'),
        ]
        
        for pattern, replacement in deprecated_patterns:
            if re.search(pattern, refactored_code):
                refactored_code = re.sub(pattern, replacement, refactored_code)
                changes.append(f"Updated deprecated pattern: {pattern}")
        
        # Update component URIs
        uri_updates = [
            ('http4:', 'http:'),
            ('https4:', 'https:'),
            ('servlet:', 'servlet:'),
            ('swagger:', 'openapi:'),
            ('metrics:', 'micrometer:'),
        ]
        
        for old_uri, new_uri in uri_updates:
            if old_uri in refactored_code:
                refactored_code = refactored_code.replace(f'"{old_uri}', f'"{new_uri}')
                refactored_code = refactored_code.replace(f"'{old_uri}", f"'{new_uri}")
                changes.append(f"Updated URI: {old_uri} -> {new_uri}")
        
        # Save refactored code
        if output_path is None:
            output_path = java_file_path
        
        with open(output_path, 'w') as f:
            f.write(refactored_code)
        
        return {
            'status': 'Success',
            'input_file': java_file_path,
            'output_file': output_path,
            'changes_made': changes,
            'change_count': len(changes),
            'message': f'Successfully refactored Java code with {len(changes)} changes'
        }
        
    except Exception as e:
        return {
            'status': 'Failure',
            'error': str(e),
            'message': f'Failed to refactor Java code: {str(e)}'
        }


def analyze_java_files(directory_path: str) -> Dict[str, Any]:
    """
    Analyze Java files in a directory for Camel usage.
    
    Args:
        directory_path: Path to directory containing Java files
        
    Returns:
        Dictionary with analysis results
    """
    try:
        java_files = []
        camel_files = []
        processors = []
        route_builders = []
        beans = []
        
        # Find all Java files
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if file.endswith('.java'):
                    file_path = os.path.join(root, file)
                    java_files.append(file_path)
                    
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                        
                        # Check for Camel imports
                        if 'import org.apache.camel' in content:
                            camel_files.append(file_path)
                            
                            # Check for specific patterns
                            if 'implements Processor' in content:
                                processors.append(file_path)
                            if 'extends RouteBuilder' in content:
                                route_builders.append(file_path)
                            if '@Component' in content or '@Bean' in content:
                                beans.append(file_path)
                    except Exception:
                        pass
        
        return {
            'status': 'Success',
            'directory': directory_path,
            'total_java_files': len(java_files),
            'camel_files': camel_files,
            'camel_file_count': len(camel_files),
            'processors': processors,
            'route_builders': route_builders,
            'beans': beans,
            'message': f'Found {len(camel_files)} Camel-related files out of {len(java_files)} Java files'
        }
        
    except Exception as e:
        return {
            'status': 'Failure',
            'error': str(e),
            'message': f'Failed to analyze Java files: {str(e)}'
        }


def create_route_builder_from_xml(xml_file_path: str, output_dir: str, package_name: str = "com.example.routes") -> Dict[str, Any]:
    """
    Create a complete RouteBuilder Java file from XML routes.

    Args:
        xml_file_path: Path to XML file with Camel routes
        output_dir: Directory to save the generated Java file
        package_name: Package name for the generated class

    Returns:
        Dictionary with conversion results
    """
    try:
        # Parse XML routes
        parsed_routes = parse_xml_routes(xml_file_path)
        if parsed_routes['status'] == 'Failure':
            return parsed_routes

        # Convert to Java DSL
        java_code = convert_xml_to_java_dsl(parsed_routes, package_name)

        # Create output directory structure
        package_path = package_name.replace('.', os.sep)
        full_output_dir = os.path.join(output_dir, package_path)
        os.makedirs(full_output_dir, exist_ok=True)

        # Generate class name from XML file name
        xml_filename = os.path.basename(xml_file_path)
        class_name = xml_filename.replace('.xml', '').replace('-', '_').title() + 'Routes'

        # Update class name in generated code
        java_code = java_code.replace('MigratedRoutes', class_name)

        # Save Java file
        output_file = os.path.join(full_output_dir, f'{class_name}.java')
        with open(output_file, 'w') as f:
            f.write(java_code)

        return {
            'status': 'Success',
            'input_file': xml_file_path,
            'output_file': output_file,
            'class_name': class_name,
            'package_name': package_name,
            'route_count': parsed_routes['route_count'],
            'message': f'Successfully converted {parsed_routes["route_count"]} routes to Java DSL'
        }

    except Exception as e:
        return {
            'status': 'Failure',
            'error': str(e),
            'message': f'Failed to create RouteBuilder: {str(e)}'
        }


# ============================================================================
# Solution 3 & 4: File Filtering and Metadata Extraction
# ============================================================================

def needs_java_migration(java_file_path: str) -> bool:
    """
    Check if a Java file needs Camel 4 migration.
    Simple filtering to avoid processing files that don't need changes.
    Also checks for Swagger and javax imports that need migration.
    """
    try:
        with open(java_file_path, 'r') as f:
            content = f.read()

        # Check for things that need migration
        has_camel_imports = 'import org.apache.camel' in content
        has_swagger_imports = 'import io.swagger.annotations' in content
        has_javax_imports = 'import javax.' in content

        # If no Camel, Swagger, or javax imports, skip
        if not (has_camel_imports or has_swagger_imports or has_javax_imports):
            return False

        # For Camel imports, skip if already migrated (has getMessage, no getIn/getOut)
        if has_camel_imports:
            has_old_api = '.getIn()' in content or '.getOut()' in content
            has_new_api = '.getMessage()' in content

            if has_new_api and not has_old_api:
                # Already Camel 4, but might still need Swagger/javax migration
                if not (has_swagger_imports or has_javax_imports):
                    return False

        # Needs migration if has:
        # - Camel old API
        # - Swagger annotations
        # - javax imports
        return True

    except Exception:
        return True  # Process on error to be safe


def needs_xml_migration(xml_file_path: str) -> bool:
    """
    Check if XML file contains Camel routes that need migration.
    """
    try:
        with open(xml_file_path, 'r') as f:
            content = f.read()

        # Check for actual route elements (not routeContextRef which contains '<route' substring)
        has_routes = ('<route ' in content or '<route>' in content or
                     'camel:route ' in content or 'camel:route>' in content)

        # Skip infrastructure files that only reference routes (no actual routes)
        if not has_routes:
            return False

        return True

    except Exception:
        return True  # Process on error


def get_java_file_metadata(java_file_path: str) -> Dict[str, Any]:
    """
    Extract lightweight metadata from Java file without loading full content to LLM.
    Returns only essential information for migration decisions.
    """
    try:
        with open(java_file_path, 'r') as f:
            content = f.read()

        lines = content.split('\n')

        return {
            'file_path': java_file_path,
            'file_name': os.path.basename(java_file_path),
            'line_count': len(lines),
            'size_bytes': len(content),
            'has_camel_imports': 'import org.apache.camel' in content,
            'is_processor': 'implements Processor' in content,
            'is_route_builder': 'extends RouteBuilder' in content,
            'uses_old_api': '.getIn()' in content or '.getOut()' in content,
            'uses_new_api': '.getMessage()' in content,
            'needs_migration': needs_java_migration(java_file_path)
        }

    except Exception as e:
        return {
            'file_path': java_file_path,
            'error': str(e),
            'needs_migration': True
        }


def get_xml_file_metadata(xml_file_path: str) -> Dict[str, Any]:
    """
    Extract lightweight metadata from XML route file.
    """
    try:
        parsed = parse_xml_routes(xml_file_path)

        with open(xml_file_path, 'r') as f:
            content = f.read()

        return {
            'file_path': xml_file_path,
            'file_name': os.path.basename(xml_file_path),
            'route_count': parsed.get('route_count', 0),
            'size_bytes': len(content),
            'has_routes': parsed.get('route_count', 0) > 0,
            'needs_migration': needs_xml_migration(xml_file_path)
        }

    except Exception as e:
        return {
            'file_path': xml_file_path,
            'error': str(e),
            'needs_migration': True
        }


# ============================================================================
# Solution 2: Large File Chunking
# ============================================================================

def parse_xml_routes_chunked(xml_file_path: str, max_routes_per_chunk: int = 10) -> List[Dict[str, Any]]:
    """
    Parse XML routes and split into chunks if file is too large.
    Returns list of route chunks for batch processing.
    """
    parsed = parse_xml_routes(xml_file_path)

    if parsed['status'] == 'Failure':
        return [parsed]

    routes = parsed.get('routes', [])
    route_count = len(routes)

    # If small enough, return as single chunk
    if route_count <= max_routes_per_chunk:
        return [parsed]

    # Split into chunks
    chunks = []
    for i in range(0, route_count, max_routes_per_chunk):
        chunk_routes = routes[i:i + max_routes_per_chunk]
        chunk = {
            'status': 'Success',
            'file_path': xml_file_path,
            'routes': chunk_routes,
            'route_count': len(chunk_routes),
            'chunk_index': i // max_routes_per_chunk,
            'total_chunks': (route_count + max_routes_per_chunk - 1) // max_routes_per_chunk,
            'message': f'Chunk {i // max_routes_per_chunk + 1} with {len(chunk_routes)} routes'
        }
        chunks.append(chunk)

    return chunks


def batch_files(file_list: List[str], batch_size: int = 5) -> List[List[str]]:
    """
    Simple utility to batch a list of files.
    """
    batches = []
    for i in range(0, len(file_list), batch_size):
        batches.append(file_list[i:i + batch_size])
    return batches
