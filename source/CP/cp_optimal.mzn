include "global_cardinality.mzn";
include "alldifferent.mzn";

% =====================
% Parameters
% =====================

int: n; 
set of int: Teams = 1..n;
set of int: Weeks = 1..(n-1);
set of int: Periods = 1..(n div 2);

% =====================
% Decision Variables
% =====================

% match[w,p,1] = home team, match[w,p,2] = away team
array[Weeks, Periods, 1..2] of var Teams: match;

% =====================
% Constraints
% =====================


% 1. each team plays exactly once per week
constraint forall(w in Weeks)(
    global_cardinality([match[w,p,s] | p in Periods, s in 1..2],
                       [t | t in Teams],
                       [1 | t in Teams]) 
);

% 2. each team plays at most twice in the same period
constraint forall(p in Periods, t in Teams) (
    sum(w in Weeks)(bool2int(match[w,p,1] = t) + bool2int(match[w,p,2] = t)) <= 2
);

% 3. each pair of teams plays exactly once (using alldifferent)
constraint forall(a in Teams, b in Teams where a < b) (
  sum(w in Weeks, p in Periods)(
    bool2int(match[w,p,1] = a /\ match[w,p,2] = b) +
    bool2int(match[w,p,1] = b /\ match[w,p,2] = a)
  ) = 1
);


% =====================
% Optimization: balance home/away fairness
% =====================
array[Teams] of var 0..(n-1): home_games;
array[Teams] of var 0..(n-1): away_games;

constraint forall(t in Teams)(
    home_games[t] = sum(w in Weeks, p in Periods)(bool2int(match[w,p,1] = t))
);

constraint forall(t in Teams)(
    away_games[t] = sum(w in Weeks, p in Periods)(bool2int(match[w,p,2] = t))
);

array[Teams] of var int: deviation;
constraint forall(t in Teams)(
    deviation[t] = abs(home_games[t] - away_games[t])
);

var int: max_dev = max(t in Teams)(deviation[t]);

% Search strategy
solve :: int_search(
    [match[w,p,s] | w in Weeks, p in Periods, s in 1..2],
    first_fail,
    indomain_min
) minimize max_dev;

% solve minimize max_dev;


% =====================
% Output
% =====================

output [
  "{\n"++
  " \"optimal\": " ++ (if show(max_dev==1)=="true" then "True" else "False" endif) ++ ",\n" ++
  " \"obj\":"++show(max_dev)++" ,\n" ++
  " \"sol\": [\n" ++
  concat([
    "  [" ++ concat([
        "[" ++ show(match[w,p,1]) ++ "," ++ show(match[w,p,2]) ++ "]"
        ++ ( if w < max(Weeks) then "," else "" endif )
      | w in Weeks]) ++ "]"
    ++ ( if p < max(Periods) then ",\n" else "\n" endif )
  | p in Periods]) ++
  " ]\n" ++
  "}\n"
];
