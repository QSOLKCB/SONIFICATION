--  SPDX-License-Identifier: MPL-2.0
--  SPARK-002 Phase 1B: bounded, caller-declared provenance only.
--  A successful audit is STRUCTURAL_ONLY_UNAUTHENTICATED, never physics.
package Spark_002_Partition with SPARK_Mode => On is
   Max_Rows : constant := 8;
   subtype Row_Index is Positive range 1 .. Max_Rows;
   subtype Row_Count is Natural range 0 .. Max_Rows;
   subtype Code is Natural range 0 .. 65_535;
   subtype Sample_Value is Integer range -1_000_000 .. 1_000_000;

   type Role_Kind is (Train, Holdout);
   type Phase_Kind is (He_I, He_II, Unknown_Phase);
   type Source_Kind is
     (Original_Processed, Secondary_Fit, Synthetic_Fixture, Unknown_Source);
   type Value_Kind is (Measured, Boundary_Zero, Missing, Invalid);
   type Reading is record
      Kind  : Value_Kind;
      Value : Sample_Value;
   end record;

   function Usable (Item : Reading) return Boolean is
     (Item.Kind = Measured or else
      (Item.Kind = Boundary_Zero and then Item.Value = 0));

   type Comparison is (Invalid_Input, Missing_Input, Below, Equal, Above);
   --  Invalid (including nonzero Boundary_Zero) takes precedence over Missing.
   --  Neither Missing nor Invalid is ever treated as a numerical zero.
   function Compare_Readings (Left, Right : Reading) return Comparison
     with Post =>
       (if Left.Kind = Invalid or else Right.Kind = Invalid or else
           (Left.Kind = Boundary_Zero and then Left.Value /= 0) or else
           (Right.Kind = Boundary_Zero and then Right.Value /= 0)
        then Compare_Readings'Result = Invalid_Input
        elsif Left.Kind = Missing or else Right.Kind = Missing
        then Compare_Readings'Result = Missing_Input
        elsif Left.Value < Right.Value
        then Compare_Readings'Result = Below
        elsif Left.Value > Right.Value
        then Compare_Readings'Result = Above
        else Compare_Readings'Result = Equal);

   type Sample_Row is record
      Row_Id           : Code;
      Campaign         : Code;
      Lab_Family       : Code;
      Run_Id           : Code;
      Document_Id      : Code;
      Measurement_Hash : Code;
      Diagnostic_Hash  : Code;
      Diagnostic_Event : Code;
      Registration     : Code;
      Role             : Role_Kind;
      Phase            : Phase_Kind;
      Source           : Source_Kind;
      Observation      : Reading;
      Calibrated_Error : Code;
      Diagnostic_Error : Code;
      Conditions_Match : Boolean;
   end record;

   --  The inactive tail must be entirely this sentinel, with no hidden rows.
   Empty_Row : constant Sample_Row :=
     (Row_Id => 0, Campaign => 0, Lab_Family => 0, Run_Id => 0,
      Document_Id => 0, Measurement_Hash => 0, Diagnostic_Hash => 0,
      Diagnostic_Event => 0, Registration => 0, Role => Train,
      Phase => Unknown_Phase, Source => Unknown_Source,
      Observation => (Kind => Missing, Value => 0),
      Calibrated_Error => 0, Diagnostic_Error => 0,
      Conditions_Match => False);

   type Row_Array is array (Row_Index) of Sample_Row;
   type Packet is record
      Count : Row_Count;
      Rows  : Row_Array;
   end record;

   --  Codes and booleans are supplied by the caller, not authenticated.
   function Declared_Row_Valid (Item : Sample_Row) return Boolean is
     (Item.Row_Id /= 0 and then Item.Campaign /= 0 and then
      Item.Lab_Family /= 0 and then Item.Run_Id /= 0 and then
      Item.Document_Id /= 0 and then Item.Measurement_Hash /= 0 and then
      Item.Diagnostic_Hash /= 0 and then Item.Diagnostic_Event /= 0 and then
      Item.Registration /= 0 and then
      Item.Measurement_Hash /= Item.Diagnostic_Hash and then
      Item.Phase /= Unknown_Phase and then
      Item.Source = Original_Processed and then
      Usable (Item.Observation) and then
      Item.Calibrated_Error /= 0 and then Item.Diagnostic_Error /= 0 and then
      Item.Conditions_Match);

   --  Duplicate rows are forbidden. Within one campaign, declared source
   --  lineage and role must agree. A source/diagnostic hash or event may
   --  repeat within that campaign, but not across different campaigns.
   --  Across TRAIN/HOLDOUT no lab family may be shared.
   function Compatible (Left, Right : Sample_Row) return Boolean is
     (Left.Row_Id /= Right.Row_Id and then
      Left.Registration = Right.Registration and then
      (if Left.Campaign = Right.Campaign then
         Left.Role = Right.Role and then
         Left.Lab_Family = Right.Lab_Family and then
         Left.Run_Id = Right.Run_Id and then
         Left.Document_Id = Right.Document_Id and then
         Left.Measurement_Hash = Right.Measurement_Hash
       else Left.Run_Id /= Right.Run_Id and then
         Left.Document_Id /= Right.Document_Id and then
         Left.Measurement_Hash /= Right.Measurement_Hash and then
         Left.Diagnostic_Hash /= Right.Diagnostic_Hash and then
         Left.Diagnostic_Event /= Right.Diagnostic_Event and then
         Left.Measurement_Hash /= Right.Diagnostic_Hash and then
         Left.Diagnostic_Hash /= Right.Measurement_Hash) and then
      (if Left.Role /= Right.Role then
         Left.Campaign /= Right.Campaign and then
         Left.Lab_Family /= Right.Lab_Family
       else True));

   function Both_Phases (Data : Packet; Role : Role_Kind) return Boolean is
     ((for some I in Row_Index =>
         I <= Data.Count and then Data.Rows (I).Role = Role and then
         Data.Rows (I).Phase = He_I)
      and then
      (for some I in Row_Index =>
         I <= Data.Count and then Data.Rows (I).Role = Role and then
         Data.Rows (I).Phase = He_II));

   --  Fixed-capacity global admission of declared structure, not evidence.
   --  Every active row is checked; every inactive slot must be exactly empty.
   function Packet_Eligible (Data : Packet) return Boolean is
     (Data.Count >= 4 and then
      (for all I in Row_Index =>
         (if I <= Data.Count then Declared_Row_Valid (Data.Rows (I))
          else Data.Rows (I) = Empty_Row)) and then
      (for all I in Row_Index =>
         (for all J in Row_Index =>
            (if I < J and then J <= Data.Count then
               Compatible (Data.Rows (I), Data.Rows (J))
             else True))) and then
      Both_Phases (Data, Train) and then Both_Phases (Data, Holdout));

   type Gate_Status is (Blocked, Structural_Only_Unauthenticated);
   type Gate_Result is record
      Status                    : Gate_Status;
      Physical_Evidence_Admitted : Boolean;
      Classifier_Score_Available : Boolean;
   end record;

   function Audit (Data : Packet) return Gate_Result
     with Post =>
       Audit'Result.Status =
         (if Packet_Eligible (Data)
          then Structural_Only_Unauthenticated else Blocked)
       and then not Audit'Result.Physical_Evidence_Admitted
       and then not Audit'Result.Classifier_Score_Available
       and then (if Audit'Result.Status = Structural_Only_Unauthenticated
                 then Packet_Eligible (Data));
end Spark_002_Partition;
