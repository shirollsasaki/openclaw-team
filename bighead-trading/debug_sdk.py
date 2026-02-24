#!/usr/bin/env python3
"""Debug Avantis SDK TradeInput fields"""

from avantis_trader_sdk.types import TradeInput
import json

# Create a minimal TradeInput to see what fields it needs
try:
    # Try creating with minimal fields
    t = TradeInput(
        trader="0x0000000000000000000000000000000000000000",
        pair_index=0,
        collateral_in_trade=1.0,
        is_long=True,
        leverage=5,
        tp=2000,
        sl=1900,
    )
    
    print("✅ TradeInput created successfully!")
    print(f"\nFields in TradeInput:")
    print(json.dumps(t.dict(), indent=2))
    
except Exception as e:
    print(f"❌ Error creating TradeInput: {e}")
    print(f"\nTrying to find required fields...")
    
    # Try to get the model fields
    try:
        fields = TradeInput.__fields__
        print(f"\nAvailable fields:")
        for name, field in fields.items():
            required = field.required
            field_type = field.type_
            print(f"  {name}: {field_type} {'(required)' if required else '(optional)'}")
    except Exception as e2:
        print(f"Could not get fields: {e2}")
