--  SPDX-License-Identifier: MPL-2.0
package body Spark_002_Core with SPARK_Mode => On is
   function Make_Box (Center : Fit_Center; Error : Fit_Error) return Fit_Box is
   begin
      return (Lower => Center - Error, Upper => Center + Error);
   end Make_Box;

   function Compare (Left, Right : Fit_Box) return Relation is
   begin
      if Left.Upper < Right.Lower then
         return A_Below_B;
      elsif Right.Upper < Left.Lower then
         return B_Below_A;
      else
         return Overlap;
      end if;
   end Compare;

   function Scale (Item : Fit_Box; Factor : Positive_Factor)
     return Wide_Box is
   begin
      return (Lower => Item.Lower * Factor, Upper => Item.Upper * Factor);
   end Scale;

   function Compare_Wide (Left, Right : Wide_Box) return Relation is
   begin
      if Left.Upper < Right.Lower then
         return A_Below_B;
      elsif Right.Upper < Left.Lower then
         return B_Below_A;
      else
         return Overlap;
      end if;
   end Compare_Wide;

   function Positive_Scale_Preserves_Order
     (Left, Right : Fit_Box; Factor : Positive_Factor) return Boolean is
   begin
      return Compare (Left, Right) =
        Compare_Wide (Scale (Left, Factor), Scale (Right, Factor));
   end Positive_Scale_Preserves_Order;

   function Evaluate (Item : Evidence) return Gate_Result is
   begin
      return
        (Status =>
           (if Structurally_Eligible (Item)
            then Structural_Only_Unauthenticated else Blocked),
         Physical_Evidence_Admitted => False,
         Classifier_Score_Available => False);
   end Evaluate;

   function Frozen_010_Decision return Gate_Result is
   begin
      return Evaluate (Frozen_010);
   end Frozen_010_Decision;
end Spark_002_Core;
