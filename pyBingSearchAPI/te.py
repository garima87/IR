def compute_eucledian(vec1, vec2):
        vector_diff = dict( (n, (vec1.get(n, 0) - vec2.get(n, 0)) **2)  for n in set(vec1)|set(vec2) )
        euc_dist = sum(vector_diff.itervalues()) **.5
        return euc_dist

vec1 = {0:1, 1:2}
vec2 = {1: 5, 2: 3}
print compute_eucledian(vec1, vec2)
