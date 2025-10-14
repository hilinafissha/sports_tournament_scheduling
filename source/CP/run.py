import json
from pathlib import Path
import minizinc
import contextlib
import io
import pprint
from datetime import timedelta
import argparse

parser = argparse.ArgumentParser()

parser.add_argument('-n', type=int, help="select the number of teams", default=0)

args = parser.parse_args()

BASE_DIR = Path(__file__).parent

print(BASE_DIR)


if args.n==0:
    N_VALUE = [6,8,10,12,14,16]
else:
    N_VALUE = [int(args.n)]


OUTPUT_DIR = Path(f'{BASE_DIR.parent.parent}/res/CP')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_NAMES = {
    "gecode_reg" :{ 'model':f'{BASE_DIR}/cp_model.mzn', 'solver':'gecode', 'opt':False  },
    "gecode_sb" :{ 'model':f'{BASE_DIR}/cp_model_sb.mzn', 'solver':'gecode', 'opt':False  },
    "gecode_opt_reg" :{ 'model':f'{BASE_DIR}/cp_optimal.mzn', 'solver':'gecode', 'opt':True  },
    # "gecode_opt_sb" :{ 'model':'cp_optimal_sb', 'solver':'gecode', 'opt':True  },
    # "chuffed_reg" :{ 'model':'cp_model', 'solver':'chuffed', 'opt':False  },
    # "chuffed_sb" :{ 'model':'cp_model_sb', 'solver':'chuffed', 'opt':False  },
    # "chuffed_opt_reg" :{ 'model':'cp_optimal', 'solver':'chuffed', 'opt':True  },
    # "chuffed_opt_sb" :{ 'model':'cp_optimal_sb', 'solver':'chuffed', 'opt':True  },
    # "cp_reg" :{ 'model':'cp_model', 'solver':'cp', 'opt':False  },
    # "cp_sb" :{ 'model':'cp_model_sb', 'solver':'cp', 'opt':False  },
    # "cp_opt_reg" :{ 'model':'cp_optimal', 'solver':'cp', 'opt':True  },
    # "cp_opt_sb" :{ 'model':'cp_optimal_sb', 'solver':'cp', 'opt':True  },
}

unsat_template = {
    'optimal':False,
    'obj':'null',
    'sol':'UNSAT',
}


# ======================
# Helper: run instance
# ======================
def run_model(model_file, solver_name, n, opt=False):
    model = minizinc.Model(model_file)
    solver = minizinc.Solver.lookup(solver_name)
    

    inst = minizinc.Instance(solver, model)
    inst["n"] = n

    print(f"Running {model_file} with {solver_name}, n={n} ...")

    with contextlib.redirect_stderr(io.StringIO()):
        result = inst.solve(timeout=timedelta(seconds=5))
        # pprint.pprint(result)
        if result.solution is None:
            return None
        output_item = eval(result.solution._output_item) 
        opt_val = output_item['optimal'] if opt else "True"
        obj_val = output_item['obj'] if opt else "null"
        sol = eval(output_item['sol']) if opt  else output_item 
    
    res = {   
            "time": (result.statistics.get("solveTime", 0)).seconds,
            "optimal":opt_val,
            "obj":obj_val,
            "sol":sol,
        }
    return res



mod_type = int(input("Select what type of models you want to run \n 1. Decision Models \n 2. Optimization Models \n 3. All\n\noption:"))
if mod_type == 1:
    model_names = {k: v for k, v in MODEL_NAMES.items() if not v.get("opt", False)}
elif mod_type == 2:
    model_names = {k: v for k, v in MODEL_NAMES.items() if v.get("opt", False)}
else:
    model_names = MODEL_NAMES
    
for n in N_VALUE:
    all_results = {}
    for model_name, model_data in model_names.items():
        # print(model_data['model'],model_data['solver'])
        output = run_model(model_data['model'],model_data['solver'],n, model_data['opt'])
        if output is None:
            print(f'(╥﹏╥) {model_name} did not find a solution for instance {n}, not adding it to the solution')
            continue
        output = {model_name:output}
        all_results.update(output)
        pprint.pprint(output)
        print('************************************')

    out_file = OUTPUT_DIR / f"{n}.json"
    with out_file.open("w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"Wrote results to {out_file}")
