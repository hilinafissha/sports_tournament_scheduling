include "alldifferent.mzn";
include "lex_less.mzn";

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
    alldifferent([match[w,p,s] | p in Periods, s in 1..2]) 
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


% =========================
% Symmetry Breaking
% =========================

% Fix the first week
constraint forall(p in Periods)(
    match[1,p,1] = 2*p - 1 /\ match[1,p,2] = 2*p
);

% Lexicographic ordering between consecutive weeks
constraint forall(w in 1..(n-2)) (
    lex_less([match[w,p,s] | p in Periods, s in 1..2],
             [match[w+1,p,s] | p in Periods, s in 1..2])
);

solve satisfy;


% =====================
% Output
% =====================

output [
  " [\n" ++
  concat([
    "  [" ++ concat([
        "[" ++ show(match[w,p,1]) ++ "," ++ show(match[w,p,2]) ++ "]"
        ++ ( if w < max(Weeks) then "," else "" endif )
      | w in Weeks]) ++ "]"
    ++ ( if p < max(Periods) then ",\n" else "\n" endif )
  | p in Periods]) ++
  " ]\n"
];
