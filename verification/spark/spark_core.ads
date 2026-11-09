--  SPDX-License-Identifier: MPL-2.0
--  QSOL-IMC: bounded, integer-only SPARK kernel. No physics admission.
package Spark_Core with SPARK_Mode => On is
   subtype Cents is Integer range -999_999 .. 999_999;
   type Evidence_Kind is (Absent, Measured, Boundary_Zero, Invalid);
   type Relation is (Missing, Below, Above, Overlap);
   type Split_Role is (Train, Holdout);

   type Interval is record
      Kind  : Evidence_Kind;
      Lower : Cents;
      Upper : Cents;
   end record;

   function Has_Value (Kind : Evidence_Kind) return Boolean is
     (Kind = Measured or else Kind = Boundary_Zero);

   function Well_Formed (Item : Interval) return Boolean is
     (Item.Lower <= Item.Upper and then
      (if Item.Kind = Boundary_Zero
       then Item.Lower = 0 and Item.Upper = 0));

   function Compare (Left, Right : Interval) return Relation
     with Pre => Well_Formed (Left) and then Well_Formed (Right),
          Post =>
            (if not Has_Value (Left.Kind) or else
                not Has_Value (Right.Kind)
             then Compare'Result = Missing
             elsif Left.Upper < Right.Lower
             then Compare'Result = Below
             elsif Right.Upper < Left.Lower
             then Compare'Result = Above
             else Compare'Result = Overlap);

   type Parse_Result is record
      Valid : Boolean;
      Value : Cents;
   end record;

   --  Format: optional "-", 1..4 integral digits, ".", 2 decimal digits.
   --  Leading-zero multiprecision representations and "+" are denied.
   --  Exact hundredths only; not a general-purpose rational parser.
   function Parse_Cents (Source : String) return Parse_Result
     with Post =>
       (if Parse_Cents'Result.Valid then
          Parse_Cents'Result.Value in Cents and
          Source'Length in 4 .. 8);

   subtype Short_Id is String (1 .. 16);
   subtype Digest_Id is String (1 .. 64);

   type Provenance is record
      Campaign : Short_Id;
      Lab : Short_Id;
      Run_Id : Short_Id;
      Document_Id : Short_Id;
      Measurement_Hash : Digest_Id;
      Diagnostic_Hash : Digest_Id;
      Diagnostic_Event : Short_Id;
      Split : Split_Role;
   end record;

   function Not_Blank (Value : String) return Boolean is
     (for some I in Value'Range => Value (I) /= ' ');

   --  Structural identity separation ONLY: these strings are not
   --  independently authenticated source or cryptographic attestations.
   function Separated (Left, Right : Provenance) return Boolean is
     (Left.Split /= Right.Split
      and then Not_Blank (Left.Campaign)
      and then Not_Blank (Right.Campaign)
      and then Not_Blank (Left.Lab)
      and then Not_Blank (Right.Lab)
      and then Not_Blank (Left.Run_Id)
      and then Not_Blank (Right.Run_Id)
      and then Not_Blank (Left.Document_Id)
      and then Not_Blank (Right.Document_Id)
      and then Not_Blank (Left.Measurement_Hash)
      and then Not_Blank (Right.Measurement_Hash)
      and then Not_Blank (Left.Diagnostic_Hash)
      and then Not_Blank (Right.Diagnostic_Hash)
      and then Not_Blank (Left.Diagnostic_Event)
      and then Not_Blank (Right.Diagnostic_Event)
      and then Left.Campaign /= Right.Campaign
      and then Left.Lab /= Right.Lab
      and then Left.Run_Id /= Right.Run_Id
      and then Left.Document_Id /= Right.Document_Id
      and then Left.Measurement_Hash /= Right.Measurement_Hash
      and then Left.Diagnostic_Hash /= Right.Diagnostic_Hash
      and then Left.Diagnostic_Event /= Right.Diagnostic_Event
      and then Left.Measurement_Hash /= Left.Diagnostic_Hash
      and then Right.Measurement_Hash /= Right.Diagnostic_Hash);
end Spark_Core;
