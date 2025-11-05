"""
Inspect LangGraph MemorySaver API to understand required methods
"""

try:
    from langgraph.checkpoint.memory import MemorySaver
    
    print("="*60)
    print("LangGraph MemorySaver API Inspection")
    print("="*60)
    
    checkpointer = MemorySaver()
    
    print("\n📋 Available Methods:")
    methods = [m for m in dir(checkpointer) if not m.startswith('_')]
    for method in sorted(methods):
        print(f"   - {method}")
    
    print("\n🔍 Method Signatures:")
    import inspect
    for method in ['put', 'get', 'list', 'get_tuple', 'aget_tuple', 'aput', 'alist', 'aput_writes']:
        if hasattr(checkpointer, method):
            sig = inspect.signature(getattr(checkpointer, method))
            print(f"\n   {method}{sig}")
        else:
            print(f"\n   {method}: NOT FOUND")
    
    print("\n" + "="*60)
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
