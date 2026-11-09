--  SPDX-License-Identifier: MPL-2.0
--  Non-SPARK differential CLI; *not* a formally analysed driver.
with Ada.Text_IO;
with Spark_002_Core;
procedure Spark_002_Probe is
   use Ada.Text_IO;
   use Spark_002_Core;

   function Next (Source : String; Cursor : in out Positive) return String is
      Start : Positive;
   begin
      while Cursor <= Source'Last and then Source (Cursor) = ' ' loop
         Cursor := Cursor + 1;
      end loop;
      Start := Cursor;
      while Cursor <= Source'Last and then Source (Cursor) /= ' ' loop
         Cursor := Cursor + 1;
      end loop;
      if Start > Source'Last then
         return "";
      end if;
      return Source (Start .. Cursor - 1);
   end Next;

   function Number (Source : String; Cursor : in out Positive) return Integer is
   begin
      return Integer'Value (Next (Source, Cursor));
   end Number;

   function Bit (Mask : Integer; Position : Natural) return Boolean is
   begin
      return (Mask / (2 ** Position)) mod 2 = 1;
   end Bit;
begin
   while not End_Of_File loop
      declare
         Source : constant String := Get_Line;
         Cursor : Positive := Source'First;
         Command : constant String := Next (Source, Cursor);
      begin
         if Command = "I" or else Command = "S" then
            declare
               A : constant Fit_Box := Make_Box
                 (Fit_Center (Number (Source, Cursor)),
                  Fit_Error (Number (Source, Cursor)));
               B : constant Fit_Box := Make_Box
                 (Fit_Center (Number (Source, Cursor)),
                  Fit_Error (Number (Source, Cursor)));
            begin
               if Command = "I" then
                  Put_Line (Relation'Image (Compare (A, B)));
               else
                  declare
                     Factor : constant Positive_Factor :=
                       Positive_Factor (Number (Source, Cursor));
                  begin
                     Put_Line (Boolean'Image
                       (Positive_Scale_Preserves_Order (A, B, Factor)));
                  end;
               end if;
            end;
         elsif Command = "G" then
            declare
               Kind : constant Integer := Number (Source, Cursor);
               Mask : constant Integer := Number (Source, Cursor);
               Campaigns : constant Integer := Number (Source, Cursor);
               Pairs : constant Integer := Number (Source, Cursor);
               Errors : constant Integer := Number (Source, Cursor);
               Diagnostics : constant Integer := Number (Source, Cursor);
            begin
               if Mask not in 0 .. 31 then
                  Put_Line ("INVALID");
               else
                  declare
                     E : constant Evidence :=
                       (Source => Source_Kind'Val (Kind),
                        Campaigns => Campaign_Count (Campaigns),
                        Independent_Pairs => Pair_Count (Pairs),
                        Calibrated_Error_Rows => Row_Count (Errors),
                        Independent_Diagnostic_Rows => Row_Count (Diagnostics),
                        Both_Phases_Train => Bit (Mask, 0),
                        Both_Phases_Holdout => Bit (Mask, 1),
                        Source_Families_Separated => Bit (Mask, 2),
                        Registration_Receipt_Present => Bit (Mask, 3),
                        Conditions_Matched => Bit (Mask, 4));
                     Decision : constant Gate_Result := Evaluate (E);
                  begin
                     if Decision.Physical_Evidence_Admitted or else
                        Decision.Classifier_Score_Available
                     then
                        Put_Line ("UNSAFE");
                     else
                        Put_Line (Gate_Status'Image (Decision.Status));
                     end if;
                  end;
               end if;
            end;
         elsif Command = "P" then
            declare
               Mode : constant Integer := Number (Source, Cursor);
               A : constant Source_Identity :=
                 (Campaign => 1, Lab_Family => 2, Run_Id => 3,
                  Document_Id => 4, Source_Hash_Code => 5,
                  Diagnostic_Hash_Code => 6, Diagnostic_Event => 7,
                  Role => Train);
               B : Source_Identity :=
                 (Campaign => 11, Lab_Family => 12, Run_Id => 13,
                  Document_Id => 14, Source_Hash_Code => 15,
                  Diagnostic_Hash_Code => 16, Diagnostic_Event => 17,
                  Role => Holdout);
            begin
               case Mode is
                  when 1 => null;
                  when 2 => B.Campaign := A.Campaign;
                  when 3 => B.Lab_Family := A.Lab_Family;
                  when 4 => B.Run_Id := A.Run_Id;
                  when 5 => B.Document_Id := A.Document_Id;
                  when 6 => B.Source_Hash_Code := A.Source_Hash_Code;
                  when 7 => B.Diagnostic_Hash_Code := A.Diagnostic_Hash_Code;
                  when 8 => B.Diagnostic_Event := A.Diagnostic_Event;
                  when 9 => B.Role := Train;
                  when 10 => B.Source_Hash_Code := B.Diagnostic_Hash_Code;
                  when 11 => B.Diagnostic_Event := 0;
                  when others => null;
               end case;
               if Mode not in 1 .. 11 then
                  Put_Line ("INVALID");
               else
                  Put_Line (Boolean'Image (Pair_Separated (A, B)));
               end if;
            end;
         elsif Command = "F" then
            declare
               Decision : constant Gate_Result := Frozen_010_Decision;
            begin
               if Decision.Status = Blocked and then
                  not Decision.Physical_Evidence_Admitted and then
                  not Decision.Classifier_Score_Available
               then
                  Put_Line ("BLOCKED_NO_SCORE");
               else
                  Put_Line ("UNSAFE");
               end if;
            end;
         else
            Put_Line ("INVALID");
         end if;
      exception
         when Constraint_Error => Put_Line ("INVALID");
      end;
   end loop;
end Spark_002_Probe;
