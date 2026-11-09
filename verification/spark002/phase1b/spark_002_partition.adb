--  SPDX-License-Identifier: MPL-2.0
package body Spark_002_Partition with SPARK_Mode => On is
   function Compare_Readings (Left, Right : Reading) return Comparison is
   begin
      if Left.Kind = Invalid or else Right.Kind = Invalid or else
        (Left.Kind = Boundary_Zero and then Left.Value /= 0) or else
        (Right.Kind = Boundary_Zero and then Right.Value /= 0)
      then
         return Invalid_Input;
      elsif Left.Kind = Missing or else Right.Kind = Missing then
         return Missing_Input;
      elsif Left.Value < Right.Value then
         return Below;
      elsif Left.Value > Right.Value then
         return Above;
      else
         return Equal;
      end if;
   end Compare_Readings;

   function Audit (Data : Packet) return Gate_Result is
   begin
      return
        (Status =>
           (if Packet_Eligible (Data)
            then Structural_Only_Unauthenticated else Blocked),
         Physical_Evidence_Admitted => False,
         Classifier_Score_Available => False);
   end Audit;
end Spark_002_Partition;
