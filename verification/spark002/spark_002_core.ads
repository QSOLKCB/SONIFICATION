--  SPDX-License-Identifier: MPL-2.0
--  SPARK-002: bounded software invariants, never independent physical admission.
package Spark_002_Core with SPARK_Mode => On is
   --  Exact signed millionths for a deliberately restricted fit domain.
   --  This is NOT a generic implementation of Python fractions.
   subtype Fit_Center is Integer range -4_000_000 .. 4_000_000;
   subtype Fit_Error is Integer range 0 .. 1_000_000;
   subtype Endpoint is Integer range -5_000_000 .. 5_000_000;
   subtype Positive_Factor is Integer range 1 .. 8;
   subtype Wide_Endpoint is Integer range -40_000_000 .. 40_000_000;

   type Fit_Box is record
      Lower : Endpoint;
      Upper : Endpoint;
   end record;
   type Wide_Box is record
      Lower : Wide_Endpoint;
      Upper : Wide_Endpoint;
   end record;
   type Relation is (A_Below_B, B_Below_A, Overlap);

   function Well_Formed (Item : Fit_Box) return Boolean is
     (Item.Lower <= Item.Upper);
   function Wide_Well_Formed (Item : Wide_Box) return Boolean is
     (Item.Lower <= Item.Upper);

   function Make_Box (Center : Fit_Center; Error : Fit_Error) return Fit_Box
     with Post =>
       Make_Box'Result.Lower = Center - Error and then
       Make_Box'Result.Upper = Center + Error and then
       Well_Formed (Make_Box'Result);

   function Compare (Left, Right : Fit_Box) return Relation
     with Pre => Well_Formed (Left) and then Well_Formed (Right),
          Post =>
            (if Left.Upper < Right.Lower
             then Compare'Result = A_Below_B
             elsif Right.Upper < Left.Lower
             then Compare'Result = B_Below_A
             else Compare'Result = Overlap);

   function Scale (Item : Fit_Box; Factor : Positive_Factor)
     return Wide_Box
     with Pre => Well_Formed (Item),
          Post =>
            Scale'Result.Lower = Item.Lower * Factor and then
            Scale'Result.Upper = Item.Upper * Factor and then
            Wide_Well_Formed (Scale'Result);

   function Compare_Wide (Left, Right : Wide_Box) return Relation
     with Pre => Wide_Well_Formed (Left) and then
                 Wide_Well_Formed (Right),
          Post =>
            (if Left.Upper < Right.Lower
             then Compare_Wide'Result = A_Below_B
             elsif Right.Upper < Left.Lower
             then Compare_Wide'Result = B_Below_A
             else Compare_Wide'Result = Overlap);

   --  A genuine cross-operation property to be proved, not inferred from tests.
   function Positive_Scale_Preserves_Order
     (Left, Right : Fit_Box; Factor : Positive_Factor) return Boolean
     with Pre => Well_Formed (Left) and then Well_Formed (Right),
          Post => Positive_Scale_Preserves_Order'Result;

   --  Identity_Code is a *caller supplied* bounded code, never a verified
   --  digest, authenticated provenance value or proof of independence.
   --  Zero represents an absent/invalid identity.
   subtype Identity_Code is Natural range 0 .. 65_535;
   type Partition is (Train, Holdout);
   type Source_Identity is record
      Campaign         : Identity_Code;
      Lab_Family       : Identity_Code;
      Run_Id           : Identity_Code;
      Document_Id      : Identity_Code;
      Source_Hash_Code : Identity_Code;
      Diagnostic_Hash_Code : Identity_Code;
      Diagnostic_Event : Identity_Code;
      Role             : Partition;
   end record;

   function Has_Identity (Item : Source_Identity) return Boolean is
     (Item.Campaign /= 0 and then Item.Lab_Family /= 0 and then
      Item.Run_Id /= 0 and then Item.Document_Id /= 0 and then
      Item.Source_Hash_Code /= 0 and then
      Item.Diagnostic_Hash_Code /= 0 and then
      Item.Diagnostic_Event /= 0 and then
      Item.Source_Hash_Code /= Item.Diagnostic_Hash_Code);

   --  Conservative pairwise TRAIN/HOLDOUT separation. Same-family cases
   --  are denied; the result cannot authenticate a real-world source.
   function Pair_Separated (Left, Right : Source_Identity)
     return Boolean is
     (Has_Identity (Left) and then Has_Identity (Right) and then
      Left.Role /= Right.Role and then
      Left.Campaign /= Right.Campaign and then
      Left.Lab_Family /= Right.Lab_Family and then
      Left.Run_Id /= Right.Run_Id and then
      Left.Document_Id /= Right.Document_Id and then
      Left.Source_Hash_Code /= Right.Source_Hash_Code and then
      Left.Diagnostic_Hash_Code /= Right.Diagnostic_Hash_Code and then
      Left.Diagnostic_Event /= Right.Diagnostic_Event);

   type Source_Kind is
     (Original_Processed, Secondary_Fit, Evaluated_Reference,
      Model_Input, Synthetic, Missing, Invalid);
   subtype Campaign_Count is Natural range 0 .. 4;
   subtype Pair_Count is Natural range 0 .. 6;
   subtype Row_Count is Natural range 0 .. 65_535;

   type Evidence is record
      Source                  : Source_Kind;
      Campaigns               : Campaign_Count;
      Independent_Pairs       : Pair_Count;
      Calibrated_Error_Rows   : Row_Count;
      Independent_Diagnostic_Rows : Row_Count;
      Both_Phases_Train       : Boolean;
      Both_Phases_Holdout     : Boolean;
      Source_Families_Separated : Boolean;
      Registration_Receipt_Present : Boolean;
      Conditions_Matched      : Boolean;
   end record;

   function Structurally_Eligible (Item : Evidence) return Boolean is
     (Item.Source = Original_Processed and then
      Item.Campaigns >= 2 and then Item.Independent_Pairs >= 1 and then
      Item.Calibrated_Error_Rows > 0 and then
      Item.Independent_Diagnostic_Rows > 0 and then
      Item.Both_Phases_Train and then Item.Both_Phases_Holdout and then
      Item.Source_Families_Separated and then
      Item.Registration_Receipt_Present and then
      Item.Conditions_Matched);

   type Gate_Status is (Blocked, Structural_Only_Unauthenticated);
   type Gate_Result is record
      Status : Gate_Status;
      Physical_Evidence_Admitted : Boolean;
      Classifier_Score_Available : Boolean;
   end record;

   function Evaluate (Item : Evidence) return Gate_Result
     with Post =>
       Evaluate'Result.Status =
         (if Structurally_Eligible (Item)
          then Structural_Only_Unauthenticated else Blocked)
       and then not Evaluate'Result.Physical_Evidence_Admitted
       and then not Evaluate'Result.Classifier_Score_Available;

   --  The *frozen* numerical admission counts recorded by MAT-SPEC-008/010.
   --  No real independent source-pair, calibrated error, or orthogonal
   --  diagnostic row is admitted. Never reinterpret these as new physics.
   Frozen_010 : constant Evidence :=
     (Source => Original_Processed, Campaigns => 1,
      Independent_Pairs => 0, Calibrated_Error_Rows => 0,
      Independent_Diagnostic_Rows => 0,
      Both_Phases_Train => False, Both_Phases_Holdout => False,
      Source_Families_Separated => False,
      Registration_Receipt_Present => False,
      Conditions_Matched => False);

   function Frozen_010_Decision return Gate_Result
     with Post =>
       Frozen_010_Decision'Result.Status = Blocked and then
       not Frozen_010_Decision'Result.Physical_Evidence_Admitted and then
       not Frozen_010_Decision'Result.Classifier_Score_Available;
end Spark_002_Core;
