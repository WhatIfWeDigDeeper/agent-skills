# Reference: Transform Rules

## Step 1. Input Normalization

Strip leading/trailing whitespace from all string fields before processing.

## Step 2. Type Coercion

Convert numeric strings to integers where the schema expects a number.

## Step 4. Field Mapping

Map incoming fields to output fields using this table:

| Input field | Output field |
|-------------|--------------|
| `user_id`   | `id`         |
| `full_name` | `name`       |
| `email_addr`| `email`      |

## Step 5. Sanitization

Remove any fields not in the field mapping table before returning output.
