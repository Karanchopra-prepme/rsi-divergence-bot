"""
Extended list of 120+ cryptocurrency pairs to monitor
"""

# Top 30 by Market Cap
TOP_COINS = [
    'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'XRP/USDT',
    'ADA/USDT', 'AVAX/USDT', 'DOT/USDT', 'MATIC/USDT', 'LINK/USDT',
    'TRX/USDT', 'ATOM/USDT', 'UNI/USDT', 'LTC/USDT', 'ETC/USDT',
    'APT/USDT', 'ARB/USDT', 'OP/USDT', 'FIL/USDT', 'NEAR/USDT',
    'VET/USDT', 'ICP/USDT', 'ALGO/USDT', 'XLM/USDT', 'HBAR/USDT',
    'INJ/USDT', 'SUI/USDT', 'SEI/USDT', 'TIA/USDT', 'FTM/USDT',
    'EGLD/USDT', 'XTZ/USDT', 'AAVE/USDT', 'AXS/USDT', 'GRT/USDT',
    'TAO/USDT','0GUSDT',
    'GIGGLE/USDT','ASTER/USDT','MMT/USDT',
]

# Mid-Cap Altcoins (30 coins)
MID_CAPS = [
    'DOGE/USDT', 'SHIB/USDT', 'PEPE/USDT', 'BONK/USDT', 'FLOKI/USDT',
    'MKR/USDT', 'SNX/USDT', 'CRV/USDT', 'COMP/USDT',
    'SUSHI/USDT', 'YFI/USDT', '1INCH/USDT', 'LDO/USDT', 'RUNE/USDT',
    'SAND/USDT', 'MANA/USDT', 'GALA/USDT', 'IMX/USDT',
    'FET/USDT', 'AGIX/USDT', 'RNDR/USDT', 'OCEAN/USDT',
    'THETA/USDT', 'ZIL/USDT', 'ENJ/USDT', 'CHZ/USDT', 'MINA/USDT',
]

# DeFi & Infrastructure (30 coins)
DEFI_COINS = [
    'CAKE/USDT', 'GMX/USDT', 'DYDX/USDT', 'BAL/USDT', 'CVX/USDT',
    'QNT/USDT', 'CELO/USDT', 'ZRX/USDT', 'BAT/USDT', 'ANT/USDT',
    'KNC/USDT', 'BNT/USDT', 'REN/USDT', 'STORJ/USDT', 'BAND/USDT',
    'KAVA/USDT', 'JST/USDT', 'SXP/USDT', 'SPELL/USDT',
    'CFX/USDT',  'CTSI/USDT', 'DATA/USDT',
    'DGB/USDT', 'EOS/USDT',
]

# Layer 2 & Scaling (20 coins)
LAYER2_COINS = [
    'LRC/USDT', 'METIS/USDT', 'SKL/USDT', 'ONE/USDT',
    'CELR/USDT', 'MOVR/USDT', 'GLMR/USDT', 'ROSE/USDT', 'PYR/USDT',
    'RAY/USDT', 'SRM/USDT', 'FIDA/USDT', 'ORCA/USDT',
     'CKB/USDT', 'RVN/USDT', 'SC/USDT', 'ZEN/USDT',
]

# Additional Popular Coins (20 coins)
POPULAR_COINS = [
    'BCH/USDT', 'XMR/USDT', 'DASH/USDT', 'ZEC/USDT', 'WAVES/USDT',
    'QTUM/USDT', 'ONT/USDT', 'ICX/USDT', 'LSK/USDT', 'NANO/USDT',
    'NEO/USDT', 'IOTA/USDT', 'OMG/USDT',
    'HOT/USDT', 'ANKR/USDT', 'DENT/USDT', 'IOTX/USDT', 'WAN/USDT',
]
EXTRA_HIGH_LIQUIDITY = [
    'XTZ/USDT',        # Tezos — mentioned in “best coins on Binance” lists. :contentReference[oaicite:4]{index=4}
    'BCH/USDT',        # Bitcoin Cash — also listed in “popular coins” group but could be emphasised.
    'XMR/USDT',        # Monero — privacy-coin, listed on Binance.
    # Zcash — another privacy crypto.
    'DASH/USDT',      # Dash - high liquidity privacy coin
    'WAVES/USDT',     # Waves - established blockchain platform
    'DOT/USDT',       # Polkadot - major infrastructure blockchain
    'LINK/USDT',      # Chainlink - leading oracle network
    'ATOM/USDT',      # Cosmos - major interoperability platform
    'AAVE/USDT',      # Aave - leading DeFi protocol
    'UNI/USDT',       # Uniswap - top DEX token
    'EOS/USDT',        # EOS — appears in high-volume lists. :contentReference[oaicite:5]{index=5}
    'FLOW/USDT',       # Flow — appears in your DEFI list, but check liquidity.
    'EGLD/USDT',       # Elrond — appears in DEFI list, verify volume.
    'KSM/USDT',        # Kusama — in DEFI list, good infrastructure play.
    'CELO/USDT',       # Celo — mobile-blockchain infrastructure listed in DEFI list.
    'REN/USDT',        # REN — infrastructure protocol, also in DEFI list.
    # plus maybe some newer but still liquid altcoins you track:
    'XTZ/USDT',
    'NEO/USDT',
    'IOTA/USDT',
]

# Combine all for 130+ coins
ALL_COINS = list(set(
    TOP_COINS + MID_CAPS + DEFI_COINS + LAYER2_COINS + POPULAR_COINS
))

# Set default to scan ALL 130+ coins
DEFAULT_WATCHLIST = ALL_COINS

def get_coins_by_category(category='all'):
    """Get coins by category"""
    categories = {
        'top': TOP_COINS,
        'mid': MID_CAPS,
        'defi': DEFI_COINS,
        'layer2': LAYER2_COINS,
        'popular': POPULAR_COINS,
        'all': ALL_COINS
    }
    return categories.get(category.lower(), ALL_COINS)

def get_coin_count():
    """Get total number of coins"""
    return len(ALL_COINS)

if __name__ == "__main__":
    print(f"Total coins: {get_coin_count()}")
    print(f"Categories:")
    print(f"  Top coins: {len(TOP_COINS)}")
    print(f"  Mid-caps: {len(MID_CAPS)}")
    print(f"  DeFi: {len(DEFI_COINS)}")
    print(f"  Layer 2: {len(LAYER2_COINS)}")
    print(f"  Popular: {len(POPULAR_COINS)}")