"""
Tool for converting Swagger v2 annotations to OpenAPI v3 annotations
"""

import re


def migrate_swagger_to_openapi(file_path: str) -> dict:
    """
    Migrate Swagger v2 annotations to OpenAPI v3 annotations in a Java file.

    Args:
        file_path: Path to Java source file

    Returns:
        Dictionary with migration results
    """
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        transformation_count = 0

        # 1. Replace Swagger imports with OpenAPI v3 imports
        swagger_import_mappings = {
            'import io.swagger.annotations.Api;': 'import io.swagger.v3.oas.annotations.tags.Tag;',
            'import io.swagger.annotations.ApiModel;': 'import io.swagger.v3.oas.annotations.media.Schema;',
            'import io.swagger.annotations.ApiModelProperty;': 'import io.swagger.v3.oas.annotations.media.Schema;',
            'import io.swagger.annotations.ApiOperation;': 'import io.swagger.v3.oas.annotations.Operation;',
            'import io.swagger.annotations.ApiParam;': 'import io.swagger.v3.oas.annotations.Parameter;',
            'import io.swagger.annotations.ApiResponse;': 'import io.swagger.v3.oas.annotations.responses.ApiResponse;',
            'import io.swagger.annotations.ApiResponses;': 'import io.swagger.v3.oas.annotations.responses.ApiResponses;'
        }

        for old_import, new_import in swagger_import_mappings.items():
            if old_import in content:
                content = content.replace(old_import, new_import)
                transformation_count += 1

        # 2. Replace @ApiModel annotations
        api_model_pattern = r'@ApiModel\s*\([^)]*(?:\n[^)]*)*\)'
        api_model_matches = list(re.finditer(api_model_pattern, content, re.MULTILINE))

        for match in api_model_matches:
            old_annotation = match.group(0)

            # Extract parameters
            params_match = re.search(r'@ApiModel\s*\((.*)\)', old_annotation, re.DOTALL)
            if params_match:
                params_str = params_match.group(1)
                params_str = ' '.join(params_str.split())

                description = None
                value = None

                desc_match = re.search(r'description\s*=\s*"([^"]*)"', params_str)
                if desc_match:
                    description = desc_match.group(1)

                value_match = re.search(r'value\s*=\s*"([^"]*)"', params_str)
                if value_match:
                    value = value_match.group(1)

                # Build new @Schema annotation
                new_params = []
                if description:
                    new_params.append(f'description = "{description}"')
                if value:
                    new_params.append(f'name = "{value}"')

                new_annotation = f'@Schema({", ".join(new_params)})' if new_params else '@Schema'
                content = content.replace(old_annotation, new_annotation)
                transformation_count += 1

        # 3. Replace @ApiModelProperty annotations with exact string matching for known patterns
        # This avoids regex complexity issues with multi-line annotations

        # Common patterns in the codebase
        api_property_replacements = [
            # Pattern 1: source field
            (
                """@ApiModelProperty(
        name = "source",
        value = "The source of this message (e.g. system, user, external service).",
        dataType = "string",
        required = true
    )""",
                """@Schema(
        name = "source",
        description = "The source of this message (e.g. system, user, external service).",
        type = "string",
        required = true
    )"""
            ),
            # Pattern 2: message field
            (
                """@ApiModelProperty(
        name = "message",
        value = "The message content.",
        dataType = "string",
        required = false
    )""",
                """@Schema(
        name = "message",
        description = "The message content.",
        type = "string",
        required = false
    )"""
            )
        ]

        # Apply known pattern replacements
        for old_pattern, new_pattern in api_property_replacements:
            if old_pattern in content:
                content = content.replace(old_pattern, new_pattern)
                transformation_count += 1

        # For any remaining @ApiModelProperty annotations, use regex
        remaining_property_pattern = r'@ApiModelProperty\s*\([^)]*(?:\n[^)]*)*\)'
        remaining_matches = list(re.finditer(remaining_property_pattern, content, re.MULTILINE))

        for match in reversed(remaining_matches):
            old_annotation = match.group(0)

            # Extract parameters
            params_match = re.search(r'@ApiModelProperty\s*\((.*)\)', old_annotation, re.DOTALL)
            if params_match:
                params_str = params_match.group(1)
                params_str = ' '.join(params_str.split())

                name = None
                value = None
                data_type = None
                required = None

                name_match = re.search(r'name\s*=\s*"([^"]*)"', params_str)
                if name_match:
                    name = name_match.group(1)

                value_match = re.search(r'value\s*=\s*"([^"]*)"', params_str)
                if value_match:
                    value = value_match.group(1)

                data_type_match = re.search(r'dataType\s*=\s*"([^"]*)"', params_str)
                if data_type_match:
                    data_type = data_type_match.group(1)

                required_match = re.search(r'required\s*=\s*(true|false)', params_str)
                if required_match:
                    required = required_match.group(1)

                # Build new @Schema annotation
                new_params = []
                if name:
                    new_params.append(f'name = "{name}"')
                if value:
                    new_params.append(f'description = "{value}"')
                if data_type:
                    new_params.append(f'type = "{data_type}"')
                if required:
                    new_params.append(f'required = {required}')

                if new_params:
                    if len(new_params) > 2:
                        # Multi-line format for readability
                        new_annotation = '@Schema(\n        ' + ',\n        '.join(new_params) + '\n    )'
                    else:
                        new_annotation = f'@Schema({", ".join(new_params)})'
                else:
                    new_annotation = '@Schema'

                content = content.replace(old_annotation, new_annotation)
                transformation_count += 1

        # 4. Replace other Swagger annotations

        # @Api -> @Tag
        api_pattern = r'@Api\s*\([^)]+\)'
        api_matches = re.finditer(api_pattern, content)
        for match in api_matches:
            old_annotation = match.group(0)
            params_match = re.search(r'@Api\s*\(([^)]+)\)', old_annotation)
            if params_match:
                params_str = params_match.group(1)

                value = None
                tags = None

                value_match = re.search(r'value\s*=\s*"([^"]*)"', params_str)
                if value_match:
                    value = value_match.group(1)

                tags_match = re.search(r'tags\s*=\s*"([^"]*)"', params_str)
                if tags_match:
                    tags = tags_match.group(1)

                new_params = []
                if value:
                    new_params.append(f'name = "{value}"')
                elif tags:
                    new_params.append(f'name = "{tags}"')

                new_annotation = f'@Tag({", ".join(new_params)})' if new_params else '@Tag'
                content = content.replace(old_annotation, new_annotation)
                transformation_count += 1

        # 5. Clean up duplicate imports
        lines = content.split('\n')
        seen_imports = set()
        cleaned_lines = []

        for line in lines:
            if line.strip().startswith('import '):
                if line not in seen_imports:
                    seen_imports.add(line)
                    cleaned_lines.append(line)
            else:
                cleaned_lines.append(line)

        content = '\n'.join(cleaned_lines)

        # Write the modified content if there were changes
        if transformation_count > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return {
                "status": "success",
                "file": file_path,
                "transformations": transformation_count,
                "message": f"Migrated {transformation_count} Swagger annotations to OpenAPI v3"
            }
        else:
            return {
                "status": "no_changes",
                "file": file_path,
                "message": "No Swagger annotations found to migrate"
            }

    except Exception as e:
        return {
            "status": "error",
            "file": file_path,
            "error": str(e),
            "message": f"Failed to migrate: {str(e)}"
        }


def migrate_jakarta_imports(file_path: str) -> dict:
    """
    Migrate javax.* imports to jakarta.* in a Java file.

    Args:
        file_path: Path to Java source file

    Returns:
        Dictionary with migration results
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        transformation_count = 0

        # Jakarta EE migration mappings
        jakarta_mappings = {
            'javax.activation': 'jakarta.activation',
            'javax.annotation': 'jakarta.annotation',
            'javax.batch': 'jakarta.batch',
            'javax.decorator': 'jakarta.decorator',
            'javax.ejb': 'jakarta.ejb',
            'javax.el': 'jakarta.el',
            'javax.enterprise': 'jakarta.enterprise',
            'javax.faces': 'jakarta.faces',
            'javax.inject': 'jakarta.inject',
            'javax.interceptor': 'jakarta.interceptor',
            'javax.jms': 'jakarta.jms',
            'javax.json': 'jakarta.json',
            'javax.jws': 'jakarta.jws',
            'javax.mail': 'jakarta.mail',
            'javax.persistence': 'jakarta.persistence',
            'javax.resource': 'jakarta.resource',
            'javax.security.auth.message': 'jakarta.security.auth.message',
            'javax.security.enterprise': 'jakarta.security.enterprise',
            'javax.security.jacc': 'jakarta.security.jacc',
            'javax.servlet': 'jakarta.servlet',
            'javax.transaction': 'jakarta.transaction',
            'javax.validation': 'jakarta.validation',
            'javax.websocket': 'jakarta.websocket',
            'javax.ws.rs': 'jakarta.ws.rs',
            'javax.xml.bind': 'jakarta.xml.bind',
            'javax.xml.soap': 'jakarta.xml.soap',
            'javax.xml.ws': 'jakarta.xml.ws'
        }

        for old_pkg, new_pkg in jakarta_mappings.items():
            count = content.count(old_pkg)
            if count > 0:
                content = content.replace(old_pkg, new_pkg)
                transformation_count += count

        if transformation_count > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return {
                "status": "success",
                "file": file_path,
                "transformations": transformation_count,
                "message": f"Migrated {transformation_count} javax references to jakarta"
            }
        else:
            return {
                "status": "no_changes",
                "file": file_path,
                "message": "No javax imports found to migrate"
            }

    except Exception as e:
        return {
            "status": "error",
            "file": file_path,
            "error": str(e),
            "message": f"Failed to migrate: {str(e)}"
        }


def migrate_content_string(content: str) -> tuple:
    """
    Apply both Swagger to OpenAPI and Jakarta migrations to a content string.

    Args:
        content: Java source code as string

    Returns:
        Tuple of (migrated_content, migration_details)
    """
    try:
        original_content = content
        transformation_count = 0
        details = {
            "swagger_transformations": 0,
            "jakarta_transformations": 0,
            "total_transformations": 0
        }

        # Apply Swagger to OpenAPI migration
        content, swagger_count = _migrate_swagger_content(content)
        details["swagger_transformations"] = swagger_count
        transformation_count += swagger_count

        # Apply Jakarta migration
        content, jakarta_count = _migrate_jakarta_content(content)
        details["jakarta_transformations"] = jakarta_count
        transformation_count += jakarta_count

        details["total_transformations"] = transformation_count

        return content, details

    except Exception as e:
        return original_content, {"error": str(e)}


def _migrate_swagger_content(content: str) -> tuple:
    """Helper to migrate Swagger annotations in content string"""
    transformation_count = 0

    # 1. Replace Swagger imports
    swagger_import_mappings = {
        'import io.swagger.annotations.Api;': 'import io.swagger.v3.oas.annotations.tags.Tag;',
        'import io.swagger.annotations.ApiModel;': 'import io.swagger.v3.oas.annotations.media.Schema;',
        'import io.swagger.annotations.ApiModelProperty;': 'import io.swagger.v3.oas.annotations.media.Schema;',
        'import io.swagger.annotations.ApiOperation;': 'import io.swagger.v3.oas.annotations.Operation;',
        'import io.swagger.annotations.ApiParam;': 'import io.swagger.v3.oas.annotations.Parameter;',
        'import io.swagger.annotations.ApiResponse;': 'import io.swagger.v3.oas.annotations.responses.ApiResponse;',
        'import io.swagger.annotations.ApiResponses;': 'import io.swagger.v3.oas.annotations.responses.ApiResponses;'
    }

    for old_import, new_import in swagger_import_mappings.items():
        if old_import in content:
            content = content.replace(old_import, new_import)
            transformation_count += 1

    # 2. Replace @ApiModel annotations
    api_model_pattern = r'@ApiModel\s*\([^)]*(?:\n[^)]*)*\)'
    api_model_matches = list(re.finditer(api_model_pattern, content, re.MULTILINE))

    for match in api_model_matches:
        old_annotation = match.group(0)

        # Extract parameters
        params_match = re.search(r'@ApiModel\s*\((.*)\)', old_annotation, re.DOTALL)
        if params_match:
            params_str = params_match.group(1)
            params_str = ' '.join(params_str.split())

            description = None
            value = None

            desc_match = re.search(r'description\s*=\s*"([^"]*)"', params_str)
            if desc_match:
                description = desc_match.group(1)

            value_match = re.search(r'value\s*=\s*"([^"]*)"', params_str)
            if value_match:
                value = value_match.group(1)

            # Build new @Schema annotation
            new_params = []
            if description:
                new_params.append(f'description = "{description}"')
            if value:
                new_params.append(f'name = "{value}"')

            new_annotation = f'@Schema({", ".join(new_params)})' if new_params else '@Schema'
            content = content.replace(old_annotation, new_annotation)
            transformation_count += 1

    # 3. Replace @ApiModelProperty with exact patterns for common cases
    api_property_replacements = [
        # Pattern 1: source field
        (
            """@ApiModelProperty(
        name = "source",
        value = "The source of this message (e.g. system, user, external service).",
        dataType = "string",
        required = true
    )""",
            """@Schema(
        name = "source",
        description = "The source of this message (e.g. system, user, external service).",
        type = "string",
        required = true
    )"""
        ),
        # Pattern 2: message field
        (
            """@ApiModelProperty(
        name = "message",
        value = "The message content.",
        dataType = "string",
        required = false
    )""",
            """@Schema(
        name = "message",
        description = "The message content.",
        type = "string",
        required = false
    )"""
        )
    ]

    # Apply known pattern replacements
    for old_pattern, new_pattern in api_property_replacements:
        if old_pattern in content:
            content = content.replace(old_pattern, new_pattern)
            transformation_count += 1

    # Handle remaining @ApiModelProperty with regex
    remaining_property_pattern = r'@ApiModelProperty\s*\([^)]*(?:\n[^)]*)*\)'
    remaining_matches = list(re.finditer(remaining_property_pattern, content, re.MULTILINE))

    for match in reversed(remaining_matches):
        old_annotation = match.group(0)

        # Extract parameters
        params_match = re.search(r'@ApiModelProperty\s*\((.*)\)', old_annotation, re.DOTALL)
        if params_match:
            params_str = params_match.group(1)
            params_str = ' '.join(params_str.split())

            name = None
            value = None
            data_type = None
            required = None

            name_match = re.search(r'name\s*=\s*"([^"]*)"', params_str)
            if name_match:
                name = name_match.group(1)

            value_match = re.search(r'value\s*=\s*"([^"]*)"', params_str)
            if value_match:
                value = value_match.group(1)

            data_type_match = re.search(r'dataType\s*=\s*"([^"]*)"', params_str)
            if data_type_match:
                data_type = data_type_match.group(1)

            required_match = re.search(r'required\s*=\s*(true|false)', params_str)
            if required_match:
                required = required_match.group(1)

            # Build new @Schema annotation
            new_params = []
            if name:
                new_params.append(f'name = "{name}"')
            if value:
                new_params.append(f'description = "{value}"')
            if data_type:
                new_params.append(f'type = "{data_type}"')
            if required:
                new_params.append(f'required = {required}')

            if new_params:
                if len(new_params) > 2:
                    # Multi-line format
                    new_annotation = '@Schema(\n        ' + ',\n        '.join(new_params) + '\n    )'
                else:
                    new_annotation = f'@Schema({", ".join(new_params)})'
            else:
                new_annotation = '@Schema'

            content = content.replace(old_annotation, new_annotation)
            transformation_count += 1

    # Clean up duplicate imports
    lines = content.split('\n')
    seen_imports = set()
    cleaned_lines = []

    for line in lines:
        if line.strip().startswith('import '):
            if line not in seen_imports:
                seen_imports.add(line)
                cleaned_lines.append(line)
        else:
            cleaned_lines.append(line)

    content = '\n'.join(cleaned_lines)

    return content, transformation_count


def _migrate_jakarta_content(content: str) -> tuple:
    """Helper to migrate jakarta imports in content string"""
    transformation_count = 0

    # Jakarta EE migration mappings
    jakarta_mappings = {
        'javax.activation': 'jakarta.activation',
        'javax.annotation': 'jakarta.annotation',
        'javax.batch': 'jakarta.batch',
        'javax.decorator': 'jakarta.decorator',
        'javax.ejb': 'jakarta.ejb',
        'javax.el': 'jakarta.el',
        'javax.enterprise': 'jakarta.enterprise',
        'javax.faces': 'jakarta.faces',
        'javax.inject': 'jakarta.inject',
        'javax.interceptor': 'jakarta.interceptor',
        'javax.jms': 'jakarta.jms',
        'javax.json': 'jakarta.json',
        'javax.jws': 'jakarta.jws',
        'javax.mail': 'jakarta.mail',
        'javax.persistence': 'jakarta.persistence',
        'javax.resource': 'jakarta.resource',
        'javax.security.auth.message': 'jakarta.security.auth.message',
        'javax.security.enterprise': 'jakarta.security.enterprise',
        'javax.security.jacc': 'jakarta.security.jacc',
        'javax.servlet': 'jakarta.servlet',
        'javax.transaction': 'jakarta.transaction',
        'javax.validation': 'jakarta.validation',
        'javax.websocket': 'jakarta.websocket',
        'javax.ws.rs': 'jakarta.ws.rs',
        'javax.xml.bind': 'jakarta.xml.bind',
        'javax.xml.soap': 'jakarta.xml.soap',
        'javax.xml.ws': 'jakarta.xml.ws'
    }

    for old_pkg, new_pkg in jakarta_mappings.items():
        count = content.count(old_pkg)
        if count > 0:
            content = content.replace(old_pkg, new_pkg)
            transformation_count += count

    return content, transformation_count


def migrate_file_completely(file_path: str) -> dict:
    """
    Apply both Swagger to OpenAPI and Jakarta migrations to a file.

    Args:
        file_path: Path to Java source file

    Returns:
        Dictionary with combined migration results
    """
    results = []

    # Apply Swagger to OpenAPI migration
    swagger_result = migrate_swagger_to_openapi(file_path)
    results.append(swagger_result)

    # Apply Jakarta migration
    jakarta_result = migrate_jakarta_imports(file_path)
    results.append(jakarta_result)

    total_transformations = sum(
        r.get('transformations', 0) for r in results
    )

    return {
        "status": "success" if total_transformations > 0 else "no_changes",
        "file": file_path,
        "swagger_migration": swagger_result,
        "jakarta_migration": jakarta_result,
        "total_transformations": total_transformations,
        "message": f"Applied {total_transformations} total transformations"
    }