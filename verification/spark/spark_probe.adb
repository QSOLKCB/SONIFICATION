--  SPDX-License-Identifier: MPL-2.0
--  Differential CLI only. This driver is Ada, not SPARK proof code.
with Ada.Text_IO;
with Spark_Core;
procedure Spark_Probe is
   use Ada.Text_IO;
   use Spark_Core;

   Line : String (1 .. 256);
   Last : Natural;

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

   function Kind (N : Integer) return Evidence_Kind is
   begin
      return Evidence_Kind'Val (N);
   end Kind;

   function Tag (X : Short_Id) return Short_Id is (X);

   function Example (Role : Split_Role) return Provenance is
      A : constant Provenance := (
         Campaign => Tag ("CAMP_A          "),
         Lab => Tag ("LAB_A           "),
         Run_Id => Tag ("RUN_A           "),
         Document_Id => Tag ("DOC_A           "),
         Measurement_Hash => (others => 'a'),
         Diagnostic_Hash => (others => 'c'),
         Diagnostic_Event => Tag ("EVENT_A         "),
         Split => Role);
   begin
      return A;
   end Example;
begin
   while not End_Of_File loop
      Get_Line (Line, Last);
      if Last = 0 then
         Put_Line ("INVALID");
      else
         declare
            Source : constant String := Line (1 .. Last);
            Cursor : Positive := Source'First;
            Command : constant String := Next (Source, Cursor);
         begin
            if Command = "I" then
               declare
                  K1 : constant Integer := Integer'Value (Next (Source, Cursor));
                  L1 : constant Integer := Integer'Value (Next (Source, Cursor));
                  H1 : constant Integer := Integer'Value (Next (Source, Cursor));
                  K2 : constant Integer := Integer'Value (Next (Source, Cursor));
                  L2 : constant Integer := Integer'Value (Next (Source, Cursor));
                  H2 : constant Integer := Integer'Value (Next (Source, Cursor));
                  A : constant Interval := (Kind (K1), Cents (L1), Cents (H1));
                  B : constant Interval := (Kind (K2), Cents (L2), Cents (H2));
               begin
                  if Well_Formed (A) and then Well_Formed (B) then
                     Put_Line (Relation'Image (Compare (A, B)));
                  else
                     Put_Line ("INVALID");
                  end if;
               end;
            elsif Command = "P" then
               declare
                  Value : constant Parse_Result :=
                    Parse_Cents (Next (Source, Cursor));
               begin
                  if Value.Valid then
                     Put_Line ("OK" & Integer'Image (Value.Value));
                  else
                     Put_Line ("INVALID");
                  end if;
               end;
            elsif Command = "L" then
               declare
                  Mode : constant Integer := Integer'Value (Next (Source, Cursor));
                  A : constant Provenance := Example (Train);
                  B : Provenance := Example (Holdout);
               begin
                  B.Campaign := "CAMP_B          ";
                  B.Lab := "LAB_B           ";
                  B.Run_Id := "RUN_B           ";
                  B.Document_Id := "DOC_B           ";
                  B.Measurement_Hash := (others => 'b');
                  B.Diagnostic_Hash := (others => 'd');
                  B.Diagnostic_Event := "EVENT_B         ";
                  case Mode is
                     when 1 => null;
                     when 2 => B.Campaign := A.Campaign;
                     when 3 => B.Lab := A.Lab;
                     when 4 => B.Run_Id := A.Run_Id;
                     when 5 => B.Document_Id := A.Document_Id;
                     when 6 => B.Measurement_Hash := A.Measurement_Hash;
                     when 7 => B.Diagnostic_Hash := A.Diagnostic_Hash;
                     when 8 => B.Diagnostic_Event := A.Diagnostic_Event;
                     when 9 => B.Split := Train;
                     when 10 => B.Campaign := (others => ' ');
                     when 11 => B.Diagnostic_Hash := B.Measurement_Hash;
                     when others => Put_Line ("INVALID");
                  end case;
                  if Mode in 1 .. 11 then
                     if Separated (A, B) then
                        Put_Line ("TRUE");
                     else
                        Put_Line ("FALSE");
                     end if;
                  end if;
               end;
            else
               Put_Line ("INVALID");
            end if;
         exception
            when Constraint_Error =>
               Put_Line ("INVALID");
         end;
      end if;
   end loop;
end Spark_Probe;
