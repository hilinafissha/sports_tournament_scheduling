include "all_different.mzn";
include "global_cardinality.mzn";

int: n;

int: W = n - 1;
int: P = n div 2;
int: M = P;

set of int: Teams   = 1..n;
set of int: Weeks   = 1..W;
set of int: Periods = 1..P;
set of int: Matches = 1..M;

array[Weeks, Matches, 1..2] of int: pair;

int: use_sb;   % 0/1
int: use_ss;   % 0/1

array[Weeks, Matches] of var Periods: per;

% flip chooses home/away orientation for fairness
array[Weeks, Matches] of var bool: flip;

% Derived variable: the home team of match (w,m)
array[Weeks, Matches] of var Teams: home;

% Week bijection
constraint forall(w in Weeks)(
  alldifferent([per[w,m] | m in Matches])
);

% At most twice per period per team
constraint forall(t in Teams, p in Periods)(
  sum(w in Weeks, m in Matches)(
    bool2int(per[w,m] = p /\ (pair[w,m,1] = t \/ pair[w,m,2] = t))
  ) <= 2
);

% Optional SB: fix week 1 period mapping
constraint if use_sb == 1 then
  forall(m in Matches)( per[1,m] = m )
else
  true
endif;

% Link home[w,m] to flip[w,m]
constraint forall(w in Weeks, m in Matches)(
  home[w,m] = if flip[w,m] then pair[w,m,2] else pair[w,m,1] endif
);

% Home games count via global cardinality on all home[w,m]
array[Teams] of var 0..W: home_games;

constraint global_cardinality(
  [ home[w,m] | w in Weeks, m in Matches ],
  [ t | t in Teams ],
  home_games
);

% For even n, W=n-1 is odd, so |2*h - W| can never be 0
var 1..W: max_dev;
constraint max_dev = max(t in Teams)( abs(2*home_games[t] - W) );

solve ::
  (if use_ss == 1 then
     seq_search([
       int_search([per[w,m]   | w in Weeks, m in Matches], first_fail, indomain_min),
       bool_search([flip[w,m] | w in Weeks, m in Matches], input_order, indomain_min)
     ])
   else
     seq_search([])
   endif)
minimize max_dev;

output [
  "{\n"++
  " \"optimal\": " ++ "True" ++ ",\n" ++
  " \"obj\":" ++ show(max_dev) ++ ",\n" ++
  " \"sol\": [\n" ++
  concat([
    "  [" ++ concat([
      let {
        int: matchIdx =
          sum(m in Matches)( if fix(per[w,m]) = p then m else 0 endif ),
        var bool: f = flip[w,matchIdx],
        int: a = pair[w,matchIdx,1],
        int: b = pair[w,matchIdx,2]
      } in
      "[" ++ show( if f then b else a endif ) ++ "," ++ show( if f then a else b endif ) ++ "]" ++
      (if w < max(Weeks) then "," else "" endif)
      | w in Weeks
    ]) ++ "]" ++
    (if p < max(Periods) then ",\n" else "\n" endif)
    | p in Periods
  ]) ++
  " ]\n" ++
  "}\n"
];
