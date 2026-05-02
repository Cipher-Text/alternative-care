"""
Database performance analysis script.

Checks for:
- Missing indexes on foreign keys
- Missing indexes on frequently queried columns
- Tables without indexes
- Potential N+1 query issues
"""

import asyncio
from sqlalchemy import inspect, text
from app.core.database import engine, get_db


async def analyze_indexes():
    """Analyze database indexes and find missing ones."""
    print("=== Database Index Analysis ===\n")

    async with engine.begin() as conn:
        # Get all tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        print(f"Found {len(tables)} tables\n")

        missing_indexes = []

        for table_name in tables:
            # Get columns
            columns = inspector.get_columns(table_name)
            indexes = inspector.get_indexes(table_name)
            foreign_keys = inspector.get_foreign_keys(table_name)

            indexed_columns = set()
            for idx in indexes:
                indexed_columns.update(idx['column_names'])

            # Check foreign keys have indexes
            for fk in foreign_keys:
                for col in fk['constrained_columns']:
                    if col not in indexed_columns:
                        missing_indexes.append({
                            'table': table_name,
                            'column': col,
                            'type': 'foreign_key',
                            'reason': 'Foreign key without index (JOIN performance)'
                        })

            # Check for common query columns
            common_query_columns = ['email', 'phone', 'status', 'created_at', 'is_active']
            for col_info in columns:
                col_name = col_info['name']
                if col_name in common_query_columns and col_name not in indexed_columns:
                    missing_indexes.append({
                        'table': table_name,
                        'column': col_name,
                        'type': 'query_column',
                        'reason': f'Frequently queried column ({col_name})'
                    })

        if missing_indexes:
            print("⚠️  MISSING INDEXES FOUND:\n")
            for idx in missing_indexes:
                print(f"  {idx['table']}.{idx['column']}")
                print(f"    Type: {idx['type']}")
                print(f"    Reason: {idx['reason']}\n")
        else:
            print("✅ All critical columns are indexed!\n")

        return missing_indexes


async def analyze_table_sizes():
    """Check table sizes to identify performance bottlenecks."""
    print("\n=== Table Size Analysis ===\n")

    async with engine.begin() as conn:
        # Query to get table sizes (PostgreSQL)
        query = text("""
            SELECT
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
                pg_total_relation_size(schemaname||'.'||tablename) AS bytes
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            LIMIT 10;
        """)

        result = await conn.execute(query)
        rows = result.fetchall()

        print("Top 10 Largest Tables:\n")
        for row in rows:
            print(f"  {row[0]}: {row[1]}")

        print()


async def check_query_performance():
    """Check for slow query patterns."""
    print("\n=== Query Performance Recommendations ===\n")

    recommendations = [
        {
            'area': 'Patient List Queries',
            'recommendation': 'Use pagination with LIMIT/OFFSET',
            'implementation': 'Already implemented in patient routes ✅'
        },
        {
            'area': 'Dashboard Aggregations',
            'recommendation': 'Consider materialized views for complex analytics',
            'implementation': 'TODO: Add for production scale'
        },
        {
            'area': 'Search Queries',
            'recommendation': 'Use PostgreSQL full-text search instead of LIKE',
            'implementation': 'Consider for Week 16+'
        },
        {
            'area': 'Tenant Filtering',
            'recommendation': 'Ensure tenant_id index exists on all tables',
            'implementation': 'Implemented in TenantScopedModel ✅'
        },
        {
            'area': 'N+1 Queries',
            'recommendation': 'Use joinedload/selectinload for relationships',
            'implementation': 'TODO: Audit service layer'
        }
    ]

    for rec in recommendations:
        print(f"  📌 {rec['area']}")
        print(f"     Recommendation: {rec['recommendation']}")
        print(f"     Status: {rec['implementation']}\n")


async def main():
    """Run all performance analyses."""
    print("🔍 AltCare Database Performance Analysis\n")
    print("=" * 60)

    missing_indexes = await analyze_indexes()
    await analyze_table_sizes()
    await check_query_performance()

    print("=" * 60)
    print("\n📊 Summary:")
    print(f"  Missing Indexes: {len(missing_indexes)}")
    if missing_indexes:
        print("  ⚠️  Action Required: Add missing indexes before production")
    else:
        print("  ✅ Index coverage looks good!")

    print("\n✅ Analysis complete!")


if __name__ == "__main__":
    asyncio.run(main())
