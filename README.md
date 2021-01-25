# Scam Transaction Scanner

This util uses a scam transactions database Etherscam DB (https://etherscamdb.info/) and measure affiliation level (Bedrin Coefficient) of the given address with scam address.
Then an algorithm called kNN (k-Nearest neighbours) classify to which class of the scammers the address affiliated with.

## The function metric:
``` python
def activation_func(x):
      return 1 / x * x if x != 0 else m.inf

def bedrin_metric(scammer, address, blocks_count, key):
    k_neg, k_pos, neg_mean_value, pos_mean_value = extract_parameters(scammer, address, blocks_count, key)
    return activation_func((k_pos * pos_mean_value) - (k_neg * neg_mean_value))
```

Just give to the bedrin_metric function scammer address, your address and some metadata and voila! 
The function will give the probability of how much it's related to the scammer address. And then it will place the address to the scammer class according to kNN.

