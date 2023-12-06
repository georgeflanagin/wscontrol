drop table if exists master;
create table master (
    t datetime default current_timestamp,
    who varchar(20),
    host varchar(20),
    command varchar(2000),
    result integer
    );

