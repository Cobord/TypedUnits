import os.path
import sys

# Tell test_perf/ about src/.
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
