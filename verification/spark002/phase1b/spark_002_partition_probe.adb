--  SPDX-License-Identifier: MPL-2.0
--  Differential-only untrusted text adapter; NOT analyzed as SPARK.
with Ada.Text_IO;
with Spark_002_Partition;
procedure Spark_002_Partition_Probe is
   use Ada.Text_IO;
   use Spark_002_Partition;

   function Next (Text : String; Cursor : in out Positive) return String is
      Start : Positive;
   begin
      while Cursor <= Text'Last and then Text (Cursor) = ' ' loop
         Cursor := Cursor + 1;
      end loop;
      Start := Cursor;
      while Cursor <= Text'Last and then Text (Cursor) /= ' ' loop
         Cursor := Cursor + 1;
      end loop;
      if Start > Text'Last then
         return "";
      end if;
      return Text (Start .. Cursor - 1);
   end Next;

   function Number (Text : String; Cursor : in out Positive) return Integer is
   begin
      return Integer'Value (Next (Text, Cursor));
   end Number;

   function Bool_Value (Text : String; Cursor : in out Positive)
     return Boolean is
      N : constant Integer := Number (Text, Cursor);
   begin
      if N not in 0 .. 1 then
         raise Constraint_Error;
      end if;
      return N = 1;
   end Bool_Value;

   procedure Require_End (Text : String; Cursor : in out Positive) is
   begin
      if Next (Text, Cursor) /= "" then
         raise Constraint_Error;
      end if;
   end Require_End;
begin
   while not End_Of_File loop
      declare
         Text   : constant String := Get_Line;
         Cursor : Positive := Text'First;
         Command : constant String := Next (Text, Cursor);
      begin
         if Command = "O" then
            declare
               Left : constant Reading :=
                 (Kind => Value_Kind'Val (Number (Text, Cursor)),
                  Value => Sample_Value (Number (Text, Cursor)));
               Right : constant Reading :=
                 (Kind => Value_Kind'Val (Number (Text, Cursor)),
                  Value => Sample_Value (Number (Text, Cursor)));
            begin
               Require_End (Text, Cursor);
               Put_Line (Comparison'Image (Compare_Readings (Left, Right)));
            end;
         elsif Command = "A" or else Command = "T" then
            declare
               Data : Packet :=
                 (Count => Row_Count (Number (Text, Cursor)),
                  Rows => (others => Empty_Row));
            begin
               for I in 1 .. Data.Count loop
                  Data.Rows (I) :=
                    (Row_Id => Code (Number (Text, Cursor)),
                     Campaign => Code (Number (Text, Cursor)),
                     Lab_Family => Code (Number (Text, Cursor)),
                     Run_Id => Code (Number (Text, Cursor)),
                     Document_Id => Code (Number (Text, Cursor)),
                     Measurement_Hash => Code (Number (Text, Cursor)),
                     Diagnostic_Hash => Code (Number (Text, Cursor)),
                     Diagnostic_Event => Code (Number (Text, Cursor)),
                     Registration => Code (Number (Text, Cursor)),
                     Role => Role_Kind'Val (Number (Text, Cursor)),
                     Phase => Phase_Kind'Val (Number (Text, Cursor)),
                     Source => Source_Kind'Val (Number (Text, Cursor)),
                     Observation =>
                       (Kind => Value_Kind'Val (Number (Text, Cursor)),
                        Value => Sample_Value (Number (Text, Cursor))),
                     Calibrated_Error => Code (Number (Text, Cursor)),
                     Diagnostic_Error => Code (Number (Text, Cursor)),
                     Conditions_Match => Bool_Value (Text, Cursor));
               end loop;
               Require_End (Text, Cursor);
               if Command = "T" then
                  if Data.Count = Max_Rows then
                     raise Constraint_Error;
                  end if;
                  Data.Rows (Data.Count + 1).Row_Id := 1;
               end if;
               declare
                  Decision : constant Gate_Result := Audit (Data);
               begin
                  if Decision.Physical_Evidence_Admitted or else
                     Decision.Classifier_Score_Available
                  then
                     Put_Line ("UNSAFE");
                  else
                     Put_Line (Gate_Status'Image (Decision.Status));
                  end if;
               end;
            end;
         else
            Put_Line ("INVALID");
         end if;
      exception
         when Constraint_Error => Put_Line ("INVALID");
      end;
   end loop;
end Spark_002_Partition_Probe;
