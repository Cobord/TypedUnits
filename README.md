## Pyfu - Fast Python Units

[![Build Status](https://matrix-reloaded.physics.ucsb.edu/teamcity/app/rest/builds/buildType:pythonunits_Pythonunits/statusIcon)](https://matrix-reloaded.physics.ucsb.edu/teamcity/project.html?projectId=pythonunits&tab=projectOverview)

Implements unit of measurement arithmetic, where a number is associated with a product of powers of base units and values with compatible units can be added.

Defines SI units, SI prefixes, and some derived units.

## Example

```python
from pyfu import Value, meter, km

print 2 * km / Value(3, 's')
print 3*meter + 5*meter
```

# Building

1. **Install dependencies**

        pip install numpy
        pip install pytest
        pip install pyparsing
        pip install Cython

2. **Cythonize**

    `python setup.py build_ext --inplace`

3. **Test**

    `py.test`
