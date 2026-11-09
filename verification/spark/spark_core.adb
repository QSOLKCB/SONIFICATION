--  SPDX-License-Identifier: MPL-2.0
package body Spark_Core with SPARK_Mode => On is
   function Compare (Left, Right : Interval) return Relation is
   begin
      if not Has_Value (Left.Kind) or else not Has_Value (Right.Kind) then
         return Missing;
      elsif Left.Upper < Right.Lower then
         return Below;
      elsif Right.Upper < Left.Lower then
         return Above;
      else
         return Overlap;
      end if;
   end Compare;

   function Parse_Cents (Source : String) return Parse_Result is
      Invalid_Result : constant Parse_Result := (Valid => False, Value => 0);
      Start_Digit : Integer := Source'First;
      --  Four integral digits and two fractional digits are the maximum.
      --  Subtype bounds also give GNATprove persistent loop facts.
      Whole : Natural range 0 .. 9_999 := 0;
      Fractional : Natural range 0 .. 99 := 0;
      Negative : Boolean := False;
   begin
      if Source'Length not in 4 .. 8 then
         return Invalid_Result;
      end if;
      if Source (Source'First) = '-' then
         Negative := True;
         Start_Digit := Start_Digit + 1;
      end if;
      --  The last three characters must be ".dd".
      if Source (Source'Last - 2) /= '.' then
         return Invalid_Result;
      end if;
      if Start_Digit > Source'Last - 3 or else
        Source'Last - 2 - Start_Digit > 4
      then
         return Invalid_Result;
      end if;
      if Start_Digit < Source'Last - 3 and then
        Source (Start_Digit) = '0'
      then
         return Invalid_Result;
      end if;
      for I in Start_Digit .. Source'Last - 3 loop
         if Source (I) not in '0' .. '9' then
            return Invalid_Result;
         end if;
         --  Defensive guard: the format check permits at most four
         --  integral digits, so this is unreachable for valid input.
         --  It makes the next multiplication and subtype assignment safe
         --  on every analysed loop iteration.
         if Whole > 999 then
            return Invalid_Result;
         end if;
         Whole := Whole * 10
           + Character'Pos (Source (I)) - Character'Pos ('0');
      end loop;
      for I in Source'Last - 1 .. Source'Last loop
         if Source (I) not in '0' .. '9' then
            return Invalid_Result;
         end if;
         --  Exactly two fractional digits are required.  As above,
         --  the guard makes the accumulator step locally provable.
         if Fractional > 9 then
            return Invalid_Result;
         end if;
         Fractional := Fractional * 10
           + Character'Pos (Source (I)) - Character'Pos ('0');
      end loop;
      if Negative then
         return (True, -(Whole * 100 + Fractional));
      else
         return (True, Whole * 100 + Fractional);
      end if;
   end Parse_Cents;
end Spark_Core;
