ALTER TABLE cards
ADD CONSTRAINT unique_library_set_foil_collector
    UNIQUE (library_id, set_name, foil, collector_num);
