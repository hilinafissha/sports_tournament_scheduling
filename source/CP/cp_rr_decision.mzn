include "all_different.mzn";

% Parameters

int: n;

int: W = n - 1;
int: P = n div 2;
int: M = P;

set of int: Teams   = 1..n;
set of int: Weeks   = 1..W;
set of int: Periods = 1..P;
set of int: Matches = 1..M;

% Fixed pairings from circle method:
array[Weeks, Matches, 1..2] of int: pair;

% Toggle symmetry breaking
int: use_sb;   % 0/1
int: use_ss;   % 0/1

% Decision Variables

array[Weeks, Matches] of var Periods: per;


% Constraints

% Each week: each period used exactly once
constraint forall(w in Weeks)(
  alldifferent([per[w,m] | m in Matches])
);

% Team appears in same period at most twice overall
constraint forall(t in Teams, p in Periods)(
  sum(w in Weeks, m in Matches)(
    bool2int(per[w,m] = p /\ (pair[w,m,1] = t \/ pair[w,m,2] = t))
  ) <= 2
);

% Symmetry Breaking

% Period labels are interchangeable -> fix week 1 mapping
constraint if use_sb == 1 then
  forall(m in Matches)( per[1,m] = m )
else
  true
endif;

% Solve / Search

solve ::
  (if use_ss == 1 then
     int_search([per[w,m] | w in Weeks, m in Matches], first_fail, indomain_min)
   else
     seq_search([])
   endif)
satisfy;


% Output (P x W)

output [
  " [\n" ++
  concat([
    "  [" ++ concat([
      let {
        int: matchIdx =
          sum(m in Matches)( if fix(per[w,m]) = p then m else 0 endif )
      } in
      "[" ++ show(pair[w,matchIdx,1]) ++ "," ++ show(pair[w,matchIdx,2]) ++ "]" ++
      (if w < max(Weeks) then "," else "" endif)
      | w in Weeks
    ]) ++ "]" ++
    (if p < max(Periods) then ",\n" else "\n" endif)
    | p in Periods
  ]) ++
  " ]\n"
];
